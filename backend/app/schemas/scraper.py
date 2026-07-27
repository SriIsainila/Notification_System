from decimal import Decimal

from pydantic import BaseModel


class ScrapedProduct(BaseModel):
    title: str | None
    price: Decimal | None
    currency: str | None
    image_url: str | None
    in_stock: bool | None
    variants: dict[str, list[str]]
    content_hash: str
    final_url: str
