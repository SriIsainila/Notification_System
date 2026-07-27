from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import text

from app.core.config import settings
from app.core.exceptions import ApplicationError
from app.database import AsyncSessionFactory, engine
from app.routes.router import api_router
from app.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if settings.scheduler_enabled:
        start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()
        await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="http://127.0.0.1:5173", status_code=307)


@app.get("/health", tags=["System"])
async def health() -> dict[str, str]:
    async with AsyncSessionFactory() as session:
        await session.execute(text("SELECT 1"))
    return {"status": "healthy", "database": "connected"}


@app.exception_handler(ApplicationError)
async def application_error_handler(_: Request, error: ApplicationError) -> JSONResponse:
    body = {"message": error.message}
    if error.details is not None:
        body["details"] = error.details
    return JSONResponse(status_code=error.status_code, content=body)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, error: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"message": "Validation failed", "details": jsonable_encoder(error.errors())},
    )

app.include_router(api_router, prefix=settings.api_prefix)
