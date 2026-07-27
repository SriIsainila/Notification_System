import pytest

from app.core.exceptions import ApplicationError
from app.utils.urls import normalize_product_url


def test_normalizes_equivalent_product_urls() -> None:
    assert normalize_product_url(
        "HTTPS://Example.COM:443/product/?utm_source=email&size=2#reviews"
    ) == "https://example.com/product?size=2"


def test_normalizes_international_domain_names() -> None:
    assert normalize_product_url("https://bücher.example/item") == (
        "https://xn--bcher-kva.example/item"
    )


@pytest.mark.parametrize(
    "url",
    [
        "https://not a host.example/item",
        "http://localhost/item",
        "http://10.0.0.1/item",
        "file:///etc/passwd",
        "https://user:secret@example.com/item",
    ],
)
def test_rejects_unsafe_or_malformed_urls(url: str) -> None:
    with pytest.raises(ApplicationError):
        normalize_product_url(url)
