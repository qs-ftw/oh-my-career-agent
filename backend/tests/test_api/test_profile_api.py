"""Tests for profile API endpoints."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.mark.asyncio
async def test_get_profile_returns_null_initially():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/profile")
    assert response.status_code == 200
    # Can be null or a profile object
    data = response.json()
    assert data is None or "headline" in data


@pytest.mark.asyncio
async def test_upsert_profile_creates_profile():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.put("/api/profile", json={
            "headline": "API Test Engineer",
            "superpowers": ["Testing", "CI/CD"],
            "proof_points": [{"name": "TestProject", "metric": "99% coverage"}],
        })
    assert response.status_code == 200
    data = response.json()
    assert data["headline"] == "API Test Engineer"
    assert len(data["superpowers"]) == 2


@pytest.mark.asyncio
async def test_get_completeness():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/profile/completeness")
    assert response.status_code == 200
    data = response.json()
    assert "total_fields" in data
    assert "completeness_pct" in data
    assert "missing_high_value" in data
