"""Tests for profile service — create, get, update, and completeness."""

from __future__ import annotations

import uuid

import pytest

from src.core.database import AsyncSessionLocal
from src.schemas.profile import CandidateProfileUpsert
from src.services import profile_service

# Use the MVP user/workspace that exists in the database
USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
WORKSPACE_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.mark.asyncio
async def test_upsert_creates_new_profile():
    async with AsyncSessionLocal() as session:
        payload = CandidateProfileUpsert(
            headline="Agent engineer focused on long-term automation",
            exit_story="Built multiple AI workflows and production services.",
            superpowers=["LangGraph orchestration", "Backend systems"],
            proof_points=[{"name": "CareerAgent", "metric": "multi-role resume orchestration"}],
        )
        profile = await profile_service.upsert_profile(
            session, USER_ID, WORKSPACE_ID, payload
        )
        await session.commit()
        assert profile.headline.startswith("Agent engineer")
        assert profile.proof_points[0]["name"] == "CareerAgent"
        assert len(profile.superpowers) == 2


@pytest.mark.asyncio
async def test_upsert_updates_existing_profile():
    async with AsyncSessionLocal() as session:
        payload1 = CandidateProfileUpsert(headline="First headline")
        await profile_service.upsert_profile(session, USER_ID, WORKSPACE_ID, payload1)
        await session.commit()

        payload2 = CandidateProfileUpsert(headline="Updated headline", superpowers=["Python"])
        profile = await profile_service.upsert_profile(session, USER_ID, WORKSPACE_ID, payload2)
        await session.commit()
        assert profile.headline == "Updated headline"
        assert profile.superpowers == ["Python"]


@pytest.mark.asyncio
async def test_get_profile_returns_created_profile():
    async with AsyncSessionLocal() as session:
        payload = CandidateProfileUpsert(headline="Test headline svc")
        await profile_service.upsert_profile(session, USER_ID, WORKSPACE_ID, payload)
        await session.commit()

        result = await profile_service.get_profile(session, USER_ID, WORKSPACE_ID)
        assert result is not None
        assert result.headline == "Test headline svc"


@pytest.mark.asyncio
async def test_completeness_with_partial_profile():
    async with AsyncSessionLocal() as session:
        payload = CandidateProfileUpsert(
            headline="Has headline",
            superpowers=["Python"],
        )
        await profile_service.upsert_profile(session, USER_ID, WORKSPACE_ID, payload)
        await session.commit()
        completeness = await profile_service.get_completeness(session, USER_ID, WORKSPACE_ID)
        assert completeness.filled_fields >= 2
        assert 0 < completeness.completeness_pct <= 100


@pytest.mark.asyncio
async def test_proof_points_roundtrip_as_structured_json():
    async with AsyncSessionLocal() as session:
        proof_points = [
            {"name": "CareerAgent", "metric": "multi-role resume orchestration"},
            {"name": "DataPipeline", "metric": "10x throughput improvement"},
        ]
        payload = CandidateProfileUpsert(
            headline="Proof point test",
            proof_points=proof_points,
        )
        profile = await profile_service.upsert_profile(session, USER_ID, WORKSPACE_ID, payload)
        await session.commit()
        assert len(profile.proof_points) == 2
        assert profile.proof_points[1]["name"] == "DataPipeline"

        # Verify roundtrip via get
        fetched = await profile_service.get_profile(session, USER_ID, WORKSPACE_ID)
        assert fetched is not None
        assert fetched.proof_points == proof_points


@pytest.mark.asyncio
async def test_one_user_gets_one_canonical_profile():
    async with AsyncSessionLocal() as session:
        payload1 = CandidateProfileUpsert(headline="Canonical first")
        await profile_service.upsert_profile(session, USER_ID, WORKSPACE_ID, payload1)
        await session.commit()

        payload2 = CandidateProfileUpsert(headline="Canonical second")
        profile = await profile_service.upsert_profile(session, USER_ID, WORKSPACE_ID, payload2)
        await session.commit()

        # Should still be the same profile (updated, not duplicated)
        assert profile.headline == "Canonical second"

        result = await profile_service.get_profile(session, USER_ID, WORKSPACE_ID)
        assert result is not None
        assert result.headline == "Canonical second"


@pytest.mark.asyncio
async def test_get_profile_context_returns_dict():
    async with AsyncSessionLocal() as session:
        payload = CandidateProfileUpsert(
            headline="Context test",
            superpowers=["Go", "Python"],
        )
        await profile_service.upsert_profile(session, USER_ID, WORKSPACE_ID, payload)
        await session.commit()

        ctx = await profile_service.get_profile_context(session, USER_ID, WORKSPACE_ID)
        assert ctx["headline"] == "Context test"
        assert ctx["superpowers"] == ["Go", "Python"]
