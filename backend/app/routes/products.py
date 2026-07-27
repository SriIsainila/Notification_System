from fastapi import APIRouter, status

from app.routes.dependencies import CurrentUser, DatabaseSession
from app.schemas.product import (
    DeleteResponse,
    ProductCreate,
    ProductRead,
    ProductStatusResponse,
    ProductUpdate,
)
from app.services.products import (
    create_product,
    delete_product,
    get_user_product,
    list_user_products,
    set_tracking_status,
    update_product,
)


router = APIRouter(prefix="/products", tags=["Products"])


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def add_url(payload: ProductCreate, session: DatabaseSession, user: CurrentUser) -> ProductRead:
    item = await create_product(session, user.user_id, payload)
    return ProductRead.from_item(item)


@router.get("", response_model=list[ProductRead])
async def list_urls(session: DatabaseSession, user: CurrentUser) -> list[ProductRead]:
    items = await list_user_products(session, user.user_id)
    return [ProductRead.from_item(item) for item in items]


@router.get("/{item_id}", response_model=ProductRead)
async def get_url(item_id: int, session: DatabaseSession, user: CurrentUser) -> ProductRead:
    item = await get_user_product(session, user.user_id, item_id)
    return ProductRead.from_item(item)


@router.patch("/{item_id}", response_model=ProductRead)
async def update_url(
    item_id: int,
    payload: ProductUpdate,
    session: DatabaseSession,
    user: CurrentUser,
) -> ProductRead:
    item = await update_product(session, user.user_id, item_id, payload)
    return ProductRead.from_item(item)


@router.delete("/{item_id}", response_model=DeleteResponse)
async def remove_url(item_id: int, session: DatabaseSession, user: CurrentUser) -> DeleteResponse:
    await delete_product(session, user.user_id, item_id)
    return DeleteResponse(message="Tracked URL deleted")


@router.post("/{item_id}/enable", response_model=ProductStatusResponse)
async def enable_tracking(
    item_id: int,
    session: DatabaseSession,
    user: CurrentUser,
) -> ProductStatusResponse:
    item = await set_tracking_status(session, user.user_id, item_id, "active")
    return ProductStatusResponse(id=item.item_id, status=item.status)


@router.post("/{item_id}/disable", response_model=ProductStatusResponse)
async def disable_tracking(
    item_id: int,
    session: DatabaseSession,
    user: CurrentUser,
) -> ProductStatusResponse:
    item = await set_tracking_status(session, user.user_id, item_id, "paused")
    return ProductStatusResponse(id=item.item_id, status=item.status)
