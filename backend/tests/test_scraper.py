from decimal import Decimal

import httpx
import pytest

from app.core.exceptions import ApplicationError
from app.services.scraper import extract_product, parse_price, scrape_product


async def public_resolver(_: str) -> list[str]:
    return ["93.184.216.34"]


def test_extracts_json_ld_product_and_variants() -> None:
    html = """
    <html><head>
      <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "Noise Cancelling Headphones",
        "image": ["https://cdn.example.com/headphones.jpg"],
        "brand": {"@type": "Brand", "name": "Nilify Audio"},
        "color": ["Black", "Silver"],
        "sku": "HP-100",
        "offers": {
          "@type": "Offer",
          "price": "8,490.00",
          "priceCurrency": "LKR",
          "availability": "https://schema.org/InStock"
        },
        "hasVariant": [
          {"@type": "Product", "name": "Black / Large", "color": "Black", "size": "Large"},
          {"@type": "Product", "name": "Silver / Small", "color": "Silver", "size": "Small"}
        ],
        "additionalProperty": {"@type": "PropertyValue", "name": "Warranty", "value": "2 years"}
      }
      </script>
    </head></html>
    """

    product = extract_product(html, "https://shop.example.com/products/headphones")

    assert product.title == "Noise Cancelling Headphones"
    assert product.price == Decimal("8490.00")
    assert product.currency == "LKR"
    assert product.image_url == "https://cdn.example.com/headphones.jpg"
    assert product.in_stock is True
    assert product.variants["brand"] == ["Nilify Audio"]
    assert product.variants["color"] == ["Black", "Silver"]
    assert product.variants["size"] == ["Large", "Small"]
    assert product.variants["warranty"] == ["2 years"]
    assert len(product.content_hash) == 64


def test_extracts_open_graph_html_and_select_variants() -> None:
    html = """
    <html><head>
      <meta property="og:title" content="Mechanical Keyboard">
      <meta property="og:image" content="/images/keyboard.jpg">
      <meta property="product:price:amount" content="1.234,56">
      <meta property="product:price:currency" content="EUR">
      <meta property="product:availability" content="out of stock">
    </head><body>
      <select name="size">
        <option value="">Choose</option>
        <option value="tkl">TKL</option>
        <option value="full">Full Size</option>
      </select>
    </body></html>
    """

    product = extract_product(html, "https://store.example.com/product")

    assert product.title == "Mechanical Keyboard"
    assert product.price == Decimal("1234.56")
    assert product.currency == "EUR"
    assert product.image_url == "https://store.example.com/images/keyboard.jpg"
    assert product.in_stock is False
    assert product.variants == {"size": ["TKL", "Full Size"]}


def test_content_hash_is_deterministic_and_changes_with_content() -> None:
    first = extract_product("<html><title>Product A</title></html>", "https://example.com/a")
    same = extract_product("<html><title>Product A</title></html>", "https://example.com/a")
    changed = extract_product("<html><title>Product B</title></html>", "https://example.com/a")

    assert first.content_hash == same.content_hash
    assert first.content_hash != changed.content_hash


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Rs. 8,490.00", Decimal("8490.00")),
        ("€1.234,56", Decimal("1234.56")),
        ("12,500", Decimal("12500")),
        ("LKR 12 500.50", Decimal("12500.50")),
        (None, None),
        ("Unavailable", None),
    ],
)
def test_price_parsing(value, expected) -> None:
    assert parse_price(value) == expected


def test_extracts_nested_json_ld_and_visible_stock_text() -> None:
    html = """
    <html><body>
      <script type="application/ld+json">
        {"@type":"ItemPage","mainEntity":{"@type":"Product","name":"Nested Product"}}
      </script>
      <p>Currently sold out</p>
    </body></html>
    """

    product = extract_product(html, "https://example.com/product")
    assert product.title == "Nested Product"
    assert product.in_stock is False


@pytest.mark.asyncio
async def test_scrapes_html_with_injected_http_client() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["accept"] == "text/html,application/xhtml+xml"
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text="<html><title>Tracked Product</title></html>",
            request=request,
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        product = await scrape_product(
            "https://example.com/product",
            client=client,
            resolver=public_resolver,
        )

    assert product.title == "Tracked Product"
    assert product.final_url == "https://example.com/product"


@pytest.mark.asyncio
async def test_validates_redirect_targets() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"location": "http://127.0.0.1/private"}, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ApplicationError, match="Private or local") as caught:
            await scrape_product(
                "https://example.com/product",
                client=client,
                resolver=public_resolver,
            )
    assert caught.value.status_code == 400


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [401, 403, 429])
async def test_reports_blocked_websites(status_code: int) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ApplicationError, match="blocked") as caught:
            await scrape_product(
                "https://example.com/product",
                client=client,
                resolver=public_resolver,
            )
    assert caught.value.status_code == 403


@pytest.mark.asyncio
async def test_reports_timeout() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow website", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ApplicationError, match="timed out") as caught:
            await scrape_product(
                "https://example.com/product",
                client=client,
                resolver=public_resolver,
            )
    assert caught.value.status_code == 504


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("content_type", "body", "message"),
    [
        ("text/html", "", "empty HTML"),
        ("application/json", '{"name":"product"}', "did not return HTML"),
        ("text/html", "<html><title>Access Denied</title></html>", "blocked"),
    ],
)
async def test_reports_missing_or_blocked_html(content_type: str, body: str, message: str) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": content_type},
            text=body,
            request=request,
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ApplicationError, match=message):
            await scrape_product(
                "https://example.com/product",
                client=client,
                resolver=public_resolver,
            )
