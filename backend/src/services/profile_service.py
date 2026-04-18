"""Database-backed service for career profile operations."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.profile import CareerProfile
from src.schemas.profile import (
    CareerProfileResponse,
    CareerProfileUpsert,
    ProfileCompletenessResponse,
)

logger = logging.getLogger(__name__)


def _to_response(p: CareerProfile) -> CareerProfileResponse:
    return CareerProfileResponse(
        id=p.id,
        name=p.name,
        headline=p.headline,
        email=p.email,
        phone=p.phone,
        linkedin_url=p.linkedin_url,
        portfolio_url=p.portfolio_url,
        github_url=p.github_url,
        location=p.location,
        professional_summary=p.professional_summary,
        skill_categories=p.skill_categories or {},
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


async def get_profile(
    session: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> CareerProfileResponse | None:
    stmt = select(CareerProfile).where(
        CareerProfile.user_id == user_id,
        CareerProfile.workspace_id == workspace_id,
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
    data: CareerProfileUpsert,
) -> CareerProfileResponse:
    stmt = select(CareerProfile).where(
        CareerProfile.user_id == user_id,
        CareerProfile.workspace_id == workspace_id,
    )
    result = await session.execute(stmt)
    profile = result.scalar_one_or_none()

    if profile is None:
        profile = CareerProfile(
            workspace_id=workspace_id,
            user_id=user_id,
        )
        session.add(profile)

    profile.name = data.name
    profile.headline = data.headline
    profile.email = data.email
    profile.phone = data.phone
    profile.linkedin_url = data.linkedin_url
    profile.portfolio_url = data.portfolio_url
    profile.github_url = data.github_url
    profile.location = data.location
    profile.professional_summary = data.professional_summary
    profile.skill_categories = data.skill_categories

    await session.flush()
    await session.refresh(profile)
    return _to_response(profile)


async def get_completeness(
    session: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> ProfileCompletenessResponse:
    profile_resp = await get_profile(session, user_id, workspace_id)

    if profile_resp is None:
        return ProfileCompletenessResponse(
            total_fields=10,
            filled_fields=0,
            completeness_pct=0.0,
            missing_high_value=["name", "headline", "email", "professional_summary", "skill_categories", "location"],
            missing_low_value=["phone", "linkedin_url", "github_url", "portfolio_url"],
        )

    high_value = {
        "name": bool(profile_resp.name),
        "headline": bool(profile_resp.headline),
        "email": bool(profile_resp.email),
        "professional_summary": bool(profile_resp.professional_summary),
        "skill_categories": bool(profile_resp.skill_categories),
        "location": bool(profile_resp.location),
    }

    low_value = {
        "phone": bool(profile_resp.phone),
        "linkedin_url": bool(profile_resp.linkedin_url),
        "github_url": bool(profile_resp.github_url),
        "portfolio_url": bool(profile_resp.portfolio_url),
    }

    # High-value fields count as 2, low-value as 1
    max_score = len(high_value) * 2 + len(low_value)
    actual_score = (
        sum(2 for v in high_value.values() if v)
        + sum(1 for v in low_value.values() if v)
    )

    missing_high = [k for k, v in high_value.items() if not v]
    missing_low = [k for k, v in low_value.items() if not v]

    filled = sum(1 for v in high_value.values() if v) + sum(1 for v in low_value.values() if v)

    return ProfileCompletenessResponse(
        total_fields=len(high_value) + len(low_value),
        filled_fields=filled,
        completeness_pct=round(actual_score / max_score * 100, 1),
        missing_high_value=missing_high,
        missing_low_value=missing_low,
    )


async def get_profile_context(
    session: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> dict:
    """Load profile as a dict for agent state injection."""
    stmt = select(CareerProfile).where(
        CareerProfile.user_id == user_id,
        CareerProfile.workspace_id == workspace_id,
    )
    result = await session.execute(stmt)
    profile = result.scalar_one_or_none()

    if profile is None:
        return {}

    return {
        "name": profile.name,
        "headline": profile.headline,
        "email": profile.email,
        "phone": profile.phone,
        "linkedin_url": profile.linkedin_url,
        "portfolio_url": profile.portfolio_url,
        "github_url": profile.github_url,
        "location": profile.location,
        "professional_summary": profile.professional_summary,
        "skill_categories": profile.skill_categories or {},
    }
