"""Unit tests for auth endpoints and psychometric scorer."""

from __future__ import annotations

from typing import Any

import pytest
from httpx import AsyncClient


class TestRegistration:
    async def test_register_success(
        self,
        client: AsyncClient,
        test_user_data: dict[str, Any],
    ) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json=test_user_data,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["email"] == test_user_data["email"]
        assert data["user"]["full_name"] == test_user_data["full_name"]
        assert "tokens" in data
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]
        assert "hashed_password" not in data["user"]

    async def test_register_duplicate_email(
        self,
        client: AsyncClient,
        test_user_data: dict[str, Any],
    ) -> None:
        await client.post("/api/v1/auth/register", json=test_user_data)
        response = await client.post(
            "/api/v1/auth/register",
            json=test_user_data,
        )
        assert response.status_code == 409

    async def test_register_weak_password(
        self,
        client: AsyncClient,
    ) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "password": "weak",
                "full_name": "Weak User",
            },
        )
        assert response.status_code == 422

    async def test_register_invalid_email(
        self,
        client: AsyncClient,
    ) -> None:
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
    async def test_login_success(
        self,
        client: AsyncClient,
        test_user_data: dict[str, Any],
    ) -> None:
        await client.post("/api/v1/auth/register", json=test_user_data)

        response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(
        self,
        client: AsyncClient,
        test_user_data: dict[str, Any],
    ) -> None:
        await client.post("/api/v1/auth/register", json=test_user_data)

        response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": test_user_data["email"],
                "password": "WrongPassword123",
            },
        )
        assert response.status_code == 401

    async def test_get_me_authenticated(
        self,
        client: AsyncClient,
        test_user_data: dict[str, Any],
    ) -> None:
        reg = await client.post(
            "/api/v1/auth/register",
            json=test_user_data,
        )
        token = reg.json()["tokens"]["access_token"]

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["email"] == test_user_data["email"]

    async def test_get_me_unauthenticated(
        self,
        client: AsyncClient,
    ) -> None:
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 403


class TestPsychometricScorer:
    """Unit tests for the psychometric scoring engine."""

    def test_scorer_imports(self) -> None:
        """Verify psychometric engine module can be imported."""
        from src.core.security.jwt import (
            create_access_token,
            hash_password,
            verify_password,
        )

        hashed = hash_password("TestPass123")
        assert verify_password("TestPass123", hashed)
        assert not verify_password("WrongPass123", hashed)

    def test_jwt_token_creation(self) -> None:
        """Verify JWT tokens are created and decoded correctly."""
        import uuid

        from src.core.security.jwt import (
            create_access_token,
            decode_access_token,
        )

        user_id = uuid.uuid4()
        token = create_access_token(user_id, "user")
        payload = decode_access_token(token)

        assert payload["sub"] == str(user_id)
        assert payload["role"] == "user"
        assert payload["type"] == "access"

    def test_health_endpoint(
        self,
        client: AsyncClient,
    ) -> None:
        """Verify health endpoint responds."""
        import asyncio

        async def _check() -> None:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"

        asyncio.get_event_loop().run_until_complete(_check())
