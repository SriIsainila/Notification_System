from decimal import Decimal
from uuid import uuid4

import psycopg
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.database import engine
from app.main import app


def database_dsn() -> str:
    return settings.database_url.replace("+asyncpg", "")


def remove_test_users(*emails: str) -> None:
    with psycopg.connect(database_dsn()) as connection:
        connection.execute("DELETE FROM users WHERE email = ANY(%s)", (list(emails),))


async def register_and_login(client: AsyncClient, email: str) -> str:
    password = "correct-horse-battery"
    register = await client.post(
        "/api/auth/register",
        json={"name": "Product Tester", "email": email, "password": password},
    )
    assert register.status_code == 201, register.text
    login = await client.post(
        "/api/auth/token",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text
    return login.json()["token"]


@pytest.mark.asyncio
async def test_product_tracking_and_ownership_flow() -> None:
    owner_email = f"products-owner-{uuid4().hex}@example.com"
    other_email = f"products-other-{uuid4().hex}@example.com"

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            owner_token = await register_and_login(client, owner_email)
            other_token = await register_and_login(client, other_email)
            owner_headers = {"Authorization": f"Bearer {owner_token}"}
            other_headers = {"Authorization": f"Bearer {other_token}"}
            client.cookies.clear()

            unauthenticated = await client.post(
                "/api/products",
                json={"url": "https://example.com/item"},
            )
            assert unauthenticated.status_code == 401

            for invalid_url in (
                "ftp://example.com/item",
                "http://localhost/item",
                "http://127.0.0.1/item",
                "https://not a host.example/item",
                "https://internal/item",
            ):
                invalid = await client.post(
                    "/api/products",
                    headers=owner_headers,
                    json={"url": invalid_url},
                )
                assert invalid.status_code == 422, invalid.text

            created = await client.post(
                "/api/products",
                headers=owner_headers,
                json={
                    "url": "https://EXAMPLE.com/product/?utm_source=newsletter",
                    "targetPrice": 9500,
                    "notifyChannel": "email",
                },
            )
            assert created.status_code == 201, created.text
            item_id = created.json()["id"]
            assert created.json()["name"] == "example.com"
            assert created.json()["status"] == "active"

            duplicate = await client.post(
                "/api/products",
                headers=owner_headers,
                json={"url": "https://example.com/product"},
            )
            assert duplicate.status_code == 409, duplicate.text

            listed = await client.get("/api/products", headers=owner_headers)
            assert listed.status_code == 200
            assert [item["id"] for item in listed.json()] == [item_id]

            updated = await client.patch(
                f"/api/products/{item_id}",
                headers=owner_headers,
                json={
                    "name": "My Product",
                    "targetPrice": 8750.50,
                    "notifyChannel": "push",
                    "checkFrequency": 120,
                },
            )
            assert updated.status_code == 200, updated.text
            assert updated.json()["name"] == "My Product"
            assert Decimal(str(updated.json()["target_price"])) == Decimal("8750.50")
            assert updated.json()["notify_channel"] == "push"
            assert updated.json()["check_frequency"] == 120

            disabled = await client.post(f"/api/products/{item_id}/disable", headers=owner_headers)
            assert disabled.status_code == 200
            assert disabled.json() == {"id": item_id, "status": "paused"}

            enabled = await client.post(f"/api/products/{item_id}/enable", headers=owner_headers)
            assert enabled.status_code == 200
            assert enabled.json() == {"id": item_id, "status": "active"}

            for method, path, json in (
                ("GET", f"/api/products/{item_id}", None),
                ("PATCH", f"/api/products/{item_id}", {"name": "Stolen"}),
                ("POST", f"/api/products/{item_id}/disable", None),
                ("POST", f"/api/products/{item_id}/enable", None),
                ("DELETE", f"/api/products/{item_id}", None),
            ):
                forbidden = await client.request(method, path, headers=other_headers, json=json)
                assert forbidden.status_code == 404, forbidden.text

            deleted = await client.delete(f"/api/products/{item_id}", headers=owner_headers)
            assert deleted.status_code == 200
            assert deleted.json()["message"] == "Tracked URL deleted"

            empty = await client.get("/api/products", headers=owner_headers)
            assert empty.status_code == 200
            assert empty.json() == []
    finally:
        await engine.dispose()
        remove_test_users(owner_email, other_email)
