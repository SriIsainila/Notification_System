from uuid import uuid4

import psycopg
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.database import AsyncSessionFactory, engine
from app.main import app
from app.models.notification import Notification


def database_dsn() -> str:
    return settings.database_url.replace("+asyncpg", "")


def remove_test_users(*emails: str) -> None:
    with psycopg.connect(database_dsn()) as connection:
        connection.execute("DELETE FROM users WHERE email = ANY(%s)", (list(emails),))


async def register_and_login(client: AsyncClient, email: str) -> tuple[int, str]:
    password = "correct-horse-battery"
    register = await client.post(
        "/api/auth/register",
        json={"name": "Notification Tester", "email": email, "password": password},
    )
    assert register.status_code == 201, register.text
    user_id = register.json()["user"]["id"]
    login = await client.post(
        "/api/auth/token",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text
    return user_id, login.json()["token"]


async def create_notifications(owner_id: int, other_id: int) -> tuple[int, int, int]:
    async with AsyncSessionFactory() as session:
        first = Notification(
            user_id=owner_id,
            message="First owner notification",
            channel="system",
            delivery_status="pending",
        )
        second = Notification(
            user_id=owner_id,
            message="Second owner notification",
            channel="email",
            delivery_status="sent",
        )
        other = Notification(
            user_id=other_id,
            message="Other user's notification",
            channel="system",
            delivery_status="pending",
        )
        session.add_all([first, second, other])
        await session.commit()
        await session.refresh(first)
        await session.refresh(second)
        await session.refresh(other)
        return first.notification_id, second.notification_id, other.notification_id


@pytest.mark.asyncio
async def test_notification_listing_reading_deletion_and_ownership() -> None:
    owner_email = f"notifications-owner-{uuid4().hex}@example.com"
    other_email = f"notifications-other-{uuid4().hex}@example.com"

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            owner_id, owner_token = await register_and_login(client, owner_email)
            other_id, other_token = await register_and_login(client, other_email)
            owner_headers = {"Authorization": f"Bearer {owner_token}"}
            other_headers = {"Authorization": f"Bearer {other_token}"}
            first_id, second_id, other_notification_id = await create_notifications(owner_id, other_id)
            client.cookies.clear()

            unauthenticated = await client.get("/api/notifications")
            assert unauthenticated.status_code == 401

            listed = await client.get("/api/notifications", headers=owner_headers)
            assert listed.status_code == 200, listed.text
            assert {item["id"] for item in listed.json()} == {first_id, second_id}
            assert all(item["message"] != "Other user's notification" for item in listed.json())

            unread = await client.get("/api/notifications/unread", headers=owner_headers)
            assert unread.status_code == 200
            assert {item["id"] for item in unread.json()} == {first_id, second_id}

            unread_query = await client.get(
                "/api/notifications",
                headers=owner_headers,
                params={"unread": "true", "limit": 1, "offset": 0},
            )
            assert unread_query.status_code == 200
            assert len(unread_query.json()) == 1

            marked = await client.patch(f"/api/notifications/{first_id}/read", headers=owner_headers)
            assert marked.status_code == 200
            assert marked.json() == {"id": first_id, "is_read": True}

            unread_after_one = await client.get("/api/notifications/unread", headers=owner_headers)
            assert [item["id"] for item in unread_after_one.json()] == [second_id]

            mark_all = await client.patch("/api/notifications/read-all", headers=owner_headers)
            assert mark_all.status_code == 200
            assert mark_all.json() == {"updated": 1}

            no_unread = await client.get("/api/notifications/unread", headers=owner_headers)
            assert no_unread.json() == []

            for method, path in (
                ("PATCH", f"/api/notifications/{other_notification_id}/read"),
                ("DELETE", f"/api/notifications/{other_notification_id}"),
            ):
                forbidden = await client.request(method, path, headers=owner_headers)
                assert forbidden.status_code == 404

            deleted = await client.delete(f"/api/notifications/{first_id}", headers=owner_headers)
            assert deleted.status_code == 200
            assert deleted.json() == {"message": "Notification deleted"}

            owner_remaining = await client.get("/api/notifications", headers=owner_headers)
            assert [item["id"] for item in owner_remaining.json()] == [second_id]

            other_list = await client.get("/api/notifications", headers=other_headers)
            assert [item["id"] for item in other_list.json()] == [other_notification_id]
    finally:
        await engine.dispose()
        remove_test_users(owner_email, other_email)
