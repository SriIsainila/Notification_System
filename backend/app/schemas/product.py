from datetime import datetime
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.exceptions import ApplicationError
from app.models.tracked_item import TrackedItem
from app.utils.urls import normalize_product_url


class ProductCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    url: str = Field(min_length=1, max_length=2000)
    target_price: Decimal | None = Field(default=None, ge=0, le=Decimal("9999999999.99"), alias="targetPrice")
    change_scope: str = Field(default="all", alias="changeScope", pattern="^(price|stock|all)$")
    notify_channel: str = Field(default="email", alias="notifyChannel", pattern="^(email|push|system)$")
    check_frequency: int = Field(default=5, ge=5, le=10080, alias="checkFrequency")

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        try:
            normalize_product_url(value)
        except ApplicationError as error:
            raise ValueError(error.message) from error
        return value.strip()


class ProductUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    url: str | None = Field(default=None, min_length=1, max_length=2000)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    target_price: Decimal | None = Field(default=None, ge=0, le=Decimal("9999999999.99"), alias="targetPrice")
    change_scope: str | None = Field(default=None, alias="changeScope", pattern="^(price|stock|all)$")
    notify_channel: str | None = Field(default=None, alias="notifyChannel", pattern="^(email|push|system)$")
    check_frequency: int | None = Field(default=None, ge=5, le=10080, alias="checkFrequency")

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            normalize_product_url(value)
        except ApplicationError as error:
            raise ValueError(error.message) from error
        return value.strip()

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        return value.strip() if value else value

    @model_validator(mode="after")
    def require_update(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one field is required")
        return self


class ProductRead(BaseModel):
    id: int
    name: str
    url: str
    image_url: str | None
    store_name: str | None
    current_price: Decimal | None
    target_price: Decimal | None
    change_scope: str
    currency: str
    in_stock: bool | None
    status: str
    notify_channel: str
    check_frequency: int
    last_checked_at: datetime | None
    created_at: datetime

    @classmethod
    def from_item(cls, item: TrackedItem) -> "ProductRead":
        return cls(
            id=item.item_id,
            name=item.title,
            url=item.url,
            image_url=item.image_url,
            store_name=item.store_name,
            current_price=item.current_price,
            target_price=item.target_price,
            change_scope=item.change_scope,
            currency=item.currency,
            in_stock=item.in_stock,
            status=item.status,
            notify_channel=item.notify_channel,
            check_frequency=item.check_frequency,
            last_checked_at=item.last_checked_at,
            created_at=item.created_at,
        )


class ProductStatusResponse(BaseModel):
    id: int
    status: str


class DeleteResponse(BaseModel):
    message: str
