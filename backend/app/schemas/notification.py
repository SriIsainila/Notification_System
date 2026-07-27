from datetime import datetime

from pydantic import BaseModel


class NotificationRead(BaseModel):
    id: int
    message: str
    channel: str
    delivery_status: str
    is_read: bool
    sent_at: datetime | None
    created_at: datetime
    change_type: str | None
    item_id: int | None
    item_title: str | None


class NotificationStatusResponse(BaseModel):
    id: int
    is_read: bool


class MarkAllReadResponse(BaseModel):
    updated: int


class DeleteNotificationResponse(BaseModel):
    message: str
