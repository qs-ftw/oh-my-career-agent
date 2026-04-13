"""Candidate profile endpoints — single canonical profile per user."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user_id, get_current_workspace_id
from src.schemas.profile import (
    CandidateProfileResponse,
    CandidateProfileUpsert,
    ProfileCompletenessResponse,
)
from src.services import profile_service

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get(
    "",
    response_model=CandidateProfileResponse | None,
    summary="Get candidate profile",
)
async def get_profile(
    db: AsyncSession = Depends(get_db),
) -> CandidateProfileResponse | None:
    """Return the current user's candidate profile, or null if not set."""
    user_id = await get_current_user_id()
    workspace_id = await get_current_workspace_id()
    return await profile_service.get_profile(db, user_id, workspace_id)


@router.put(
    "",
    response_model=CandidateProfileResponse,
    summary="Create or update candidate profile",
)
async def upsert_profile(
    body: CandidateProfileUpsert,
    db: AsyncSession = Depends(get_db),
) -> CandidateProfileResponse:
    """Upsert the current user's candidate profile."""
    user_id = await get_current_user_id()
    workspace_id = await get_current_workspace_id()
    return await profile_service.upsert_profile(db, user_id, workspace_id, body)


@router.get(
    "/completeness",
    response_model=ProfileCompletenessResponse,
    summary="Get profile completeness metrics",
)
async def get_completeness(
    db: AsyncSession = Depends(get_db),
) -> ProfileCompletenessResponse:
    """Return profile completeness metrics."""
    user_id = await get_current_user_id()
    workspace_id = await get_current_workspace_id()
    return await profile_service.get_completeness(db, user_id, workspace_id)
