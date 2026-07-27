from fastapi import APIRouter

from app.routes.auth import router as auth_router
from app.routes.notifications import router as notifications_router
from app.routes.products import router as products_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(products_router)
api_router.include_router(notifications_router)
