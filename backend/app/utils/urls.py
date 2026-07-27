import ipaddress
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.core.exceptions import ApplicationError


TRACKING_QUERY_KEYS = {"fbclid", "gclid", "mc_cid", "mc_eid"}
DOMAIN_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


def normalize_product_url(value: str) -> str:
    raw_url = value.strip()
    if len(raw_url) > 2000:
        raise ApplicationError("URL must not exceed 2000 characters")

    try:
        parsed = urlsplit(raw_url)
        port = parsed.port
    except ValueError as error:
        raise ApplicationError("Invalid product URL") from error

    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise ApplicationError("Only HTTP and HTTPS product URLs are allowed")
    if parsed.username or parsed.password:
        raise ApplicationError("URLs containing credentials are not allowed")

    hostname = parsed.hostname.rstrip(".").lower()
    try:
        hostname = hostname.encode("idna").decode("ascii")
    except UnicodeError as error:
        raise ApplicationError("Invalid product URL hostname") from error
    if hostname == "localhost" or hostname.endswith((".localhost", ".local")):
        raise ApplicationError("Private or local URLs are not allowed")

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address and not address.is_global:
        raise ApplicationError("Private or local URLs are not allowed")
    if address is None:
        labels = hostname.split(".")
        if len(labels) < 2 or len(hostname) > 253 or any(not DOMAIN_LABEL.fullmatch(label) for label in labels):
            raise ApplicationError("Invalid product URL hostname")

    scheme = parsed.scheme.lower()
    default_port = (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    formatted_host = f"[{hostname}]" if address and address.version == 6 else hostname
    netloc = formatted_host if port is None or default_port else f"{formatted_host}:{port}"
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/") or "/"

    query_items = [
        (key, item)
        for key, item in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in TRACKING_QUERY_KEYS
    ]
    query = urlencode(sorted(query_items))
    return urlunsplit((scheme, netloc, path, query, ""))


def hostname_from_url(value: str) -> str:
    hostname = urlsplit(value).hostname
    return (hostname or "Tracked product").removeprefix("www.")
