"""Integration tests for the careers and profile API endpoints."""

from __future__ import annotations

from typing import Any
import uuid

from httpx import AsyncClient


def unique_user() -> dict[str, Any]:
    uid = uuid.uuid4().hex[:8]
    return {
        "email": f"rec_{uid}@example.com",
        "password": "TestPassword123",
        "full_name": f"Rec User {uid}",
    }


async def register_and_token(client: AsyncClient) -> str:
    """Register a new user and return their access token."""
    user = unique_user()
    resp = await client.post("/api/v1/auth/register", json=user)
    assert resp.status_code == 201
    return resp.json()["tokens"]["access_token"]


class TestProfileEndpoints:
    async def test_get_profile_creates_blank_if_missing(self, client: AsyncClient) -> None:
        token = await register_and_token(client)
        resp = await client.get(
            "/api/v1/profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["onboarding_completed"] is False
        assert data["completeness_score"] == 0.0

    async def test_patch_profile_updates_fields(self, client: AsyncClient) -> None:
        token = await register_and_token(client)
        resp = await client.patch(
            "/api/v1/profile",
            json={
                "education_level": "Bachelor's degree",
                "current_field": "Technology",
                "primary_goal": "Become a software architect",
                "country": "India",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["education_level"] == "Bachelor's degree"
        assert data["current_field"] == "Technology"
        assert data["country"] == "India"

    async def test_patch_profile_increases_completeness(self, client: AsyncClient) -> None:
        token = await register_and_token(client)
        resp = await client.patch(
            "/api/v1/profile",
            json={
                "education_level": "Master's degree",
                "current_field": "Engineering",
                "primary_goal": "Lead engineering teams",
                "country": "US",
                "years_of_experience": 5,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["completeness_score"] > 0.0

    async def test_patch_profile_rejects_invalid_experience(self, client: AsyncClient) -> None:
        token = await register_and_token(client)
        resp = await client.patch(
            "/api/v1/profile",
            json={"years_of_experience": -5},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_get_profile_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/profile")
        assert resp.status_code in (401, 403)

    async def test_patch_profile_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.patch("/api/v1/profile", json={"country": "US"})
        assert resp.status_code in (401, 403)


class TestCareersEndpoints:
    async def test_recommendations_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/careers/recommendations")
        assert resp.status_code in (401, 403)

    async def test_recommendations_without_assessment_returns_400(
        self, client: AsyncClient
    ) -> None:
        token = await register_and_token(client)
        resp = await client.get(
            "/api/v1/careers/recommendations",
            headers={"Authorization": f"Bearer {token}"},
        )
        # Either 400 (no assessment) or 404 (no profile) — both correct before onboarding
        assert resp.status_code in (400, 404)

    async def test_recommendations_top_k_param_validates(self, client: AsyncClient) -> None:
        token = await register_and_token(client)
        resp = await client.get(
            "/api/v1/careers/recommendations?top_k=200",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_recommendations_top_k_zero_validates(self, client: AsyncClient) -> None:
        token = await register_and_token(client)
        resp = await client.get(
            "/api/v1/careers/recommendations?top_k=0",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422
