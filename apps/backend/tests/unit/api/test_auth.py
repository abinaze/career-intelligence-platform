"""Unit tests for auth endpoints and JWT security."""

from __future__ import annotations

import uuid
from typing import Any

from httpx import AsyncClient


def unique_user() -> dict[str, Any]:
    """Generate unique user data for each test to avoid DB conflicts."""
    uid = uuid.uuid4().hex[:8]
    return {
        "email": f"test_{uid}@example.com",
        "password": "TestPassword123",
        "full_name": f"Test User {uid}",
    }


class TestRegistration:
    async def test_register_success(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json=unique_user(),
        )
        assert response.status_code == 201
        data = response.json()
        assert "tokens" in data
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]
        assert "hashed_password" not in data["user"]

    async def test_register_duplicate_email(self, client: AsyncClient) -> None:
        user = unique_user()
        await client.post("/api/v1/auth/register", json=user)
        response = await client.post("/api/v1/auth/register", json=user)
        assert response.status_code == 409

    async def test_register_weak_password(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "password": "weak",
                "full_name": "Weak User",
            },
        )
        assert response.status_code == 422

    async def test_register_invalid_email(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "StrongPass123",
                "full_name": "Test User",
            },
        )
        assert response.status_code == 422


class TestLogin:
    async def test_login_success(self, client: AsyncClient) -> None:
        user = unique_user()
        await client.post("/api/v1/auth/register", json=user)
        response = await client.post(
            "/api/v1/auth/token",
            data={"username": user["email"], "password": user["password"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient) -> None:
        user = unique_user()
        await client.post("/api/v1/auth/register", json=user)
        response = await client.post(
            "/api/v1/auth/token",
            data={"username": user["email"], "password": "WrongPassword123"},
        )
        assert response.status_code == 401

    async def test_get_me_authenticated(self, client: AsyncClient) -> None:
        user = unique_user()
        reg = await client.post("/api/v1/auth/register", json=user)
        token = reg.json()["tokens"]["access_token"]
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["email"] == user["email"]

    async def test_get_me_no_token(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/auth/me")
        assert response.status_code in (401, 403)


class TestJWT:
    """Pure unit tests — no database or HTTP client needed."""

    def test_password_hashing(self) -> None:
        from src.core.security.jwt import hash_password, verify_password

        hashed = hash_password("TestPass123")
        assert verify_password("TestPass123", hashed)
        assert not verify_password("WrongPass123", hashed)

    def test_access_token_creation_and_decode(self) -> None:
        from src.core.security.jwt import create_access_token, decode_access_token

        user_id = uuid.uuid4()
        token = create_access_token(user_id, "user")
        payload = decode_access_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["role"] == "user"
        assert payload["type"] == "access"

    def test_hash_token_is_deterministic(self) -> None:
        from src.core.security.jwt import hash_token

        token = "some-refresh-token-value"
        assert hash_token(token) == hash_token(token)
        assert len(hash_token(token)) == 64
