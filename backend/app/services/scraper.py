import asyncio
import hashlib
import ipaddress
import json
import re
from collections.abc import Awaitable, Callable, Iterable
from decimal import Decimal, InvalidOperation
from socket import AF_UNSPEC, SOCK_STREAM
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.exceptions import ApplicationError
from app.schemas.scraper import ScrapedProduct
from app.utils.urls import normalize_product_url


Resolver = Callable[[str], Awaitable[list[str]]]
BLOCKED_STATUSES = {401, 403, 407, 429}
REDIRECT_STATUSES = {301, 302, 303, 307, 308}
BLOCK_PAGE_MARKERS = (
    "access denied",
    "cf-chl-",
    "verify you are human",
    "unusual traffic",
    "captcha challenge",
)


async def resolve_hostname(hostname: str) -> list[str]:
    loop = asyncio.get_running_loop()
    records = await loop.getaddrinfo(hostname, None, family=AF_UNSPEC, type=SOCK_STREAM)
    return sorted({record[4][0] for record in records})


async def validate_public_url(value: str, resolver: Resolver = resolve_hostname) -> str:
    try:
        normalized = normalize_product_url(value)
    except ApplicationError:
        raise

    hostname = httpx.URL(normalized).host
    try:
        addresses = await resolver(hostname)
    except (OSError, UnicodeError) as error:
        raise ApplicationError("Product website could not be resolved", status_code=400) from error
    if not addresses:
        raise ApplicationError("Product website could not be resolved", status_code=400)

    for value in addresses:
        try:
            address = ipaddress.ip_address(value)
        except ValueError as error:
            raise ApplicationError("Product website resolved to an invalid address", status_code=400) from error
        if not address.is_global:
            raise ApplicationError("Private or local URLs are not allowed", status_code=400)
    return normalized


def parse_price(value: Any) -> Decimal | None:
    if value is None:
        return None
    raw_value = re.sub(r"(?<=\d)[\s\u00a0](?=\d)", "", str(value))
    candidates = re.findall(r"-?\d[\d,.]*", raw_value)
    text = max(candidates, key=len) if candidates else ""
    if not text or text in {"-", ".", ","}:
        return None

    comma = text.rfind(",")
    dot = text.rfind(".")
    if comma >= 0 and dot >= 0:
        decimal_separator = "," if comma > dot else "."
        thousands_separator = "." if decimal_separator == "," else ","
        text = text.replace(thousands_separator, "").replace(decimal_separator, ".")
    elif comma >= 0 or dot >= 0:
        separator = "," if comma >= 0 else "."
        parts = text.split(separator)
        if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3):
            text = "".join(parts)
        else:
            text = text.replace(separator, ".")

    try:
        price = Decimal(text)
    except InvalidOperation:
        return None
    return price if price >= 0 else None


def find_json_ld_products(soup: BeautifulSoup) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []

    def visit(value: Any) -> None:
        if isinstance(value, list):
            for item in value:
                visit(item)
            return
        if not isinstance(value, dict):
            return
        product_type = value.get("@type")
        types = product_type if isinstance(product_type, list) else [product_type]
        if any(str(item).lower() == "product" for item in types):
            products.append(value)
            return
        for nested in value.values():
            visit(nested)

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            visit(json.loads(script.get_text(strip=True)))
        except (json.JSONDecodeError, TypeError):
            continue
    return products


def first_offer(product: dict[str, Any]) -> dict[str, Any]:
    offers = product.get("offers") or {}
    if isinstance(offers, list):
        return next((offer for offer in offers if isinstance(offer, dict)), {})
    return offers if isinstance(offers, dict) else {}


def meta_content(soup: BeautifulSoup, *keys: str) -> str | None:
    for key in keys:
        tag = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key})
        if tag and tag.get("content"):
            return str(tag["content"]).strip()
    return None


def value_list(value: Any) -> list[str]:
    source: Iterable[Any] = value if isinstance(value, list) else [value]
    result: list[str] = []
    for item in source:
        if isinstance(item, dict):
            item = item.get("name") or item.get("value")
        if item is not None and str(item).strip():
            result.append(str(item).strip())
    return list(dict.fromkeys(result))


def extract_variants(soup: BeautifulSoup, product: dict[str, Any]) -> dict[str, list[str]]:
    variants: dict[str, list[str]] = {}

    def add(name: str, value: Any) -> None:
        values = value_list(value)
        if values:
            variants.setdefault(name.lower(), [])
            variants[name.lower()] = list(dict.fromkeys([*variants[name.lower()], *values]))

    for field in ("color", "size", "sku", "model", "material", "pattern"):
        add(field, product.get(field))
    brand = product.get("brand")
    add("brand", brand)

    properties = product.get("additionalProperty") or []
    if isinstance(properties, dict):
        properties = [properties]
    for item in properties:
        if isinstance(item, dict) and item.get("name"):
            add(str(item["name"]), item.get("value"))

    product_variants = product.get("hasVariant") or []
    if isinstance(product_variants, dict):
        product_variants = [product_variants]
    for variant in product_variants:
        if isinstance(variant, dict):
            add("variant", variant.get("name"))
            for field in ("color", "size", "sku", "model", "material", "pattern"):
                add(field, variant.get(field))
        else:
            add("variant", variant)

    for select in soup.find_all("select"):
        name = select.get("name") or select.get("id") or select.get("aria-label")
        if not name:
            continue
        options = [
            option.get_text(" ", strip=True)
            for option in select.find_all("option")
            if option.get_text(" ", strip=True)
            and not option.has_attr("disabled")
            and str(option.get("value", "")).lower() not in {"", "select", "choose"}
        ]
        add(str(name), options)
    return dict(sorted(variants.items()))


def stock_from_availability(value: Any) -> bool | None:
    text = re.sub(r"[^a-z]", "", str(value or "").lower())
    if any(marker in text for marker in ("outofstock", "soldout", "discontinued")):
        return False
    if any(marker in text for marker in ("instock", "limitedavailability", "preorder", "backorder")):
        return True
    return None


def content_hash_for(data: dict[str, Any]) -> str:
    serialized = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def extract_product(html: str, final_url: str) -> ScrapedProduct:
    soup = BeautifulSoup(html, "html.parser")
    product = (find_json_ld_products(soup) or [{}])[0]
    offer = first_offer(product)

    title = product.get("name") or meta_content(soup, "og:title", "twitter:title")
    if not title and soup.title:
        title = soup.title.get_text(" ", strip=True)
    title = str(title).strip()[:255] if title else None

    price_value = (
        offer.get("price")
        or offer.get("lowPrice")
        or meta_content(soup, "product:price:amount", "og:price:amount")
    )
    if price_value is None:
        price_node = soup.find(attrs={"itemprop": "price"})
        if price_node:
            price_value = price_node.get("content") or price_node.get_text(" ", strip=True)
    price = parse_price(price_value)

    currency = (
        offer.get("priceCurrency")
        or meta_content(soup, "product:price:currency", "og:price:currency")
    )
    currency = str(currency).upper()[:10] if currency else None

    image = product.get("image") or meta_content(soup, "og:image", "twitter:image")
    if isinstance(image, list):
        image = next((item for item in image if item), None)
    if isinstance(image, dict):
        image = image.get("url") or image.get("contentUrl")
    image_url = urljoin(final_url, str(image).strip()) if image else None

    availability = offer.get("availability") or meta_content(soup, "product:availability")
    if availability is None:
        availability_node = soup.find(attrs={"itemprop": "availability"}) or soup.find(
            attrs={"data-stock-status": True}
        )
        if availability_node:
            availability = availability_node.get("content") or availability_node.get_text(" ", strip=True)
    if availability is None:
        visible_text = soup.get_text(" ", strip=True)[:200_000].lower()
        if "out of stock" in visible_text or "sold out" in visible_text:
            availability = "out of stock"
        elif re.search(r"\bin stock\b", visible_text):
            availability = "in stock"
    in_stock = stock_from_availability(availability)
    variants = extract_variants(soup, product)

    state = {
        "title": title,
        "price": str(price) if price is not None else None,
        "currency": currency,
        "image_url": image_url,
        "in_stock": in_stock,
        "variants": variants,
    }
    return ScrapedProduct(
        **state,
        content_hash=content_hash_for(state),
        final_url=final_url,
    )


async def read_html(response: httpx.Response) -> str:
    content_length = response.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > settings.scraper_max_bytes:
        raise ApplicationError("Product page is too large", status_code=422)

    body = bytearray()
    async for chunk in response.aiter_bytes():
        body.extend(chunk)
        if len(body) > settings.scraper_max_bytes:
            raise ApplicationError("Product page is too large", status_code=422)

    content_type = response.headers.get("content-type", "").lower()
    text = body.decode(response.encoding or "utf-8", errors="replace").strip()
    if not text:
        raise ApplicationError("Product website returned empty HTML", status_code=422)
    if content_type and "text/html" not in content_type and "application/xhtml+xml" not in content_type:
        raise ApplicationError("Product URL did not return HTML", status_code=422)
    if not content_type and not re.match(r"(?is)^\s*(?:<!doctype\s+html|<html|<head|<body|<meta)", text):
        raise ApplicationError("Product URL did not return HTML", status_code=422)
    if any(marker in text[:200_000].lower() for marker in BLOCK_PAGE_MARKERS):
        raise ApplicationError("Product website blocked the scraper", status_code=403)
    return text


async def scrape_product(
    url: str,
    *,
    client: httpx.AsyncClient | None = None,
    resolver: Resolver = resolve_hostname,
) -> ScrapedProduct:
    current_url = await validate_public_url(url, resolver)
    owns_client = client is None
    if client is None:
        client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.scraper_timeout_seconds),
            headers={
                "User-Agent": settings.scraper_user_agent,
                "Accept": "text/html,application/xhtml+xml",
            },
            follow_redirects=False,
        )

    try:
        for redirect_count in range(settings.scraper_max_redirects + 1):
            async with client.stream(
                "GET",
                current_url,
                headers={
                    "User-Agent": settings.scraper_user_agent,
                    "Accept": "text/html,application/xhtml+xml",
                },
            ) as response:
                if response.status_code in BLOCKED_STATUSES:
                    raise ApplicationError("Product website blocked the scraper", status_code=403)
                if response.status_code in REDIRECT_STATUSES:
                    location = response.headers.get("location")
                    if not location or redirect_count >= settings.scraper_max_redirects:
                        raise ApplicationError("Too many product website redirects", status_code=422)
                    current_url = await validate_public_url(urljoin(current_url, location), resolver)
                    continue
                if response.status_code >= 400:
                    raise ApplicationError(
                        f"Product website returned HTTP {response.status_code}",
                        status_code=422,
                    )
                html = await read_html(response)
                return extract_product(html, current_url)
    except (httpx.TimeoutException, asyncio.TimeoutError) as error:
        raise ApplicationError("Product website request timed out", status_code=504) from error
    except httpx.RequestError as error:
        raise ApplicationError("Could not download product website", status_code=502) from error
    finally:
        if owns_client:
            await client.aclose()

    raise ApplicationError("Could not download product website", status_code=502)
