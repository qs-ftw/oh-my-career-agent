"""Database-backed service for candidate profile operations."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.profile import CandidateProfile
from src.schemas.profile import (
    CandidateProfileResponse,
    CandidateProfileUpsert,
    ProfileCompletenessResponse,
)

logger = logging.getLogger(__name__)


def _to_response(profile: CandidateProfile) -> CandidateProfileResponse:
    """Convert a CandidateProfile ORM instance to CandidateProfileResponse."""
    return CandidateProfileResponse(
        id=profile.id,
        headline=profile.headline,
        exit_story=profile.exit_story,
        superpowers=profile.superpowers_json or [],
        proof_points=profile.proof_points_json or [],
        compensation=profile.compensation_json or {},
        location=profile.location_json or {},
        preferences=profile.preferences_json or {},
        constraints=profile.constraints_json or {},
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


async def get_profile(
    session: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> CandidateProfileResponse | None:
    """Return the candidate profile for the given user, or None."""
    stmt = select(CandidateProfile).where(
        CandidateProfile.user_id == user_id,
        CandidateProfile.workspace_id == workspace_id,
    )
    result = await session.execute(stmt)
    profile = result.scalar_one_or_none()
    if profile is None:
        return None
    return _to_response(profile)


async def upsert_profile(
    session: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    data: CandidateProfileUpsert,
) -> CandidateProfileResponse:
    """Create or update the candidate profile (one per user per workspace)."""
    stmt = select(CandidateProfile).where(
        CandidateProfile.user_id == user_id,
        CandidateProfile.workspace_id == workspace_id,
    )
    result = await session.execute(stmt)
    profile = result.scalar_one_or_none()

    if profile is None:
        profile = CandidateProfile(
            workspace_id=workspace_id,
            user_id=user_id,
        )
        session.add(profile)

    profile.headline = data.headline
    profile.exit_story = data.exit_story
    profile.superpowers_json = data.superpowers
    profile.proof_points_json = data.proof_points
    profile.compensation_json = data.compensation
    profile.location_json = data.location
    profile.preferences_json = data.preferences
    profile.constraints_json = data.constraints

    await session.flush()
    await session.refresh(profile)
    return _to_response(profile)


async def get_completeness(
    session: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> ProfileCompletenessResponse:
    """Calculate profile completeness metrics."""
    profile_resp = await get_profile(session, user_id, workspace_id)

    if profile_resp is None:
        return ProfileCompletenessResponse(
            total_fields=8,
            filled_fields=0,
            completeness_pct=0.0,
            missing_high_value=["headline", "superpowers", "proof_points"],
        )

    high_value_fields = {
        "headline": bool(profile_resp.headline),
        "exit_story": bool(profile_resp.exit_story),
        "superpowers": bool(profile_resp.superpowers),
        "proof_points": bool(profile_resp.proof_points),
        "compensation": bool(profile_resp.compensation),
        "location": bool(profile_resp.location),
        "preferences": bool(profile_resp.preferences),
        "constraints": bool(profile_resp.constraints),
    }

    filled = sum(1 for v in high_value_fields.values() if v)
    total = len(high_value_fields)
    missing = [k for k, v in high_value_fields.items() if not v]

    return ProfileCompletenessResponse(
        total_fields=total,
        filled_fields=filled,
        completeness_pct=round(filled / total * 100, 1),
        missing_high_value=missing,
    )


async def get_profile_context(
    session: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> dict:
    """Load profile as a dict for agent state injection.

    Returns an empty dict if no profile exists, so downstream nodes
    can safely access it without null checks.
    """
    stmt = select(CandidateProfile).where(
        CandidateProfile.user_id == user_id,
        CandidateProfile.workspace_id == workspace_id,
    )
    result = await session.execute(stmt)
    profile = result.scalar_one_or_none()

    if profile is None:
        return {}

    return {
        "headline": profile.headline,
        "exit_story": profile.exit_story,
        "superpowers": profile.superpowers_json or [],
        "proof_points": profile.proof_points_json or [],
        "compensation": profile.compensation_json or {},
        "location": profile.location_json or {},
        "preferences": profile.preferences_json or {},
        "constraints": profile.constraints_json or {},
    }
