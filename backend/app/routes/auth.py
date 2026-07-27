from fastapi import APIRouter, Response, status

from app.routes.dependencies import CurrentUser, DatabaseSession
from app.core.config import settings
from app.schemas.user import (
    CurrentUserResponse,
    LoginResponse,
    LogoutResponse,
    RegisterResponse,
    TokenResponse,
    UserLogin,
    UserRead,
    UserRegister,
)
from app.services.auth import authenticate_user, issue_user_token, register_user


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, session: DatabaseSession) -> RegisterResponse:
    user = await register_user(session, payload)
    return RegisterResponse(user=UserRead.from_user(user))


@router.post("/login", response_model=LoginResponse)
async def login(payload: UserLogin, response: Response, session: DatabaseSession) -> LoginResponse:
    user = await authenticate_user(session, payload.email, payload.password)
    token = issue_user_token(user)
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        max_age=settings.jwt_expire_minutes * 60,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        path="/",
    )
    return LoginResponse(user=UserRead.from_user(user))


@router.post("/token", response_model=TokenResponse)
async def token(payload: UserLogin, session: DatabaseSession) -> TokenResponse:
    user = await authenticate_user(session, payload.email, payload.password)
    return TokenResponse(token=issue_user_token(user), user=UserRead.from_user(user))


@router.get("/me", response_model=CurrentUserResponse)
async def me(current_user: CurrentUser) -> CurrentUserResponse:
    return CurrentUserResponse(user=UserRead.from_user(current_user))


@router.post("/logout", response_model=LogoutResponse)
async def logout(response: Response) -> LogoutResponse:
    response.delete_cookie(
        key=settings.auth_cookie_name,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        path="/",
    )
    return LogoutResponse(message="Logged out")
