from uuid import uuid4

import psycopg
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.database import engine
from app.main import app


def database_dsn() -> str:
    return settings.database_url.replace("+asyncpg", "")


def remove_test_user(email: str) -> None:
    with psycopg.connect(database_dsn()) as connection:
        connection.execute("DELETE FROM users WHERE email = %s", (email,))


@pytest.mark.asyncio
async def test_complete_authentication_flow() -> None:
    email = f"auth-{uuid4().hex}@example.com"
    password = "correct-horse-battery"

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            register = await client.post(
                "/api/auth/register",
                json={"name": "  Test User  ", "email": email.upper(), "password": password},
            )
            assert register.status_code == 201, register.text
            assert register.json()["user"]["name"] == "Test User"
            assert register.json()["user"]["email"] == email
            assert "password" not in register.text

            duplicate = await client.post(
                "/api/auth/register",
                json={"name": "Test User", "email": email, "password": password},
            )
            assert duplicate.status_code == 409
            assert duplicate.json()["message"] == "An account with this email already exists"

            wrong_login = await client.post(
                "/api/auth/login",
                json={"email": email, "password": "incorrect-password"},
            )
            assert wrong_login.status_code == 401
            assert wrong_login.json()["message"] == "Invalid email or password"

            missing_token = await client.get("/api/auth/me")
            assert missing_token.status_code == 401

            login = await client.post(
                "/api/auth/login",
                json={"email": email, "password": password},
            )
            assert login.status_code == 200, login.text
            assert "token" not in login.json()
            assert login.json()["user"]["email"] == email
            cookie_header = login.headers["set-cookie"].lower()
            assert settings.auth_cookie_name in cookie_header
            assert "httponly" in cookie_header
            assert "samesite=lax" in cookie_header

            cookie_user = await client.get("/api/auth/me")
            assert cookie_user.status_code == 200, cookie_user.text
            assert cookie_user.json()["user"]["email"] == email

            token_response = await client.post(
                "/api/auth/token",
                json={"email": email, "password": password},
            )
            assert token_response.status_code == 200
            token = token_response.json()["token"]

            current_user = await client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert current_user.status_code == 200, current_user.text
            assert current_user.json()["user"]["email"] == email

            invalid_token = await client.get(
                "/api/auth/me",
                headers={"Authorization": "Bearer invalid"},
            )
            assert invalid_token.status_code == 401

            logout = await client.post("/api/auth/logout")
            assert logout.status_code == 200
            assert logout.json() == {"message": "Logged out"}
            logged_out = await client.get("/api/auth/me")
            assert logged_out.status_code == 401
    finally:
        await engine.dispose()
        remove_test_user(email)


@pytest.mark.asyncio
async def test_registration_validation_error_shape() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/auth/register",
            json={"name": "X", "email": "invalid", "password": "short"},
        )

    assert response.status_code == 422
    assert response.json()["message"] == "Validation failed"
    assert isinstance(response.json()["details"], list)
