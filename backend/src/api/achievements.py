"""Achievement endpoints — stubs returning mock data."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Path, status

from src.schemas.achievement import AchievementCreate, AchievementResponse
from src.services import achievement_service

router = APIRouter(prefix="/achievements", tags=["achievements"])


@router.post(
    "",
    response_model=AchievementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new achievement",
)
async def create_achievement(body: AchievementCreate) -> AchievementResponse:
    """Submit a new raw achievement for processing."""
    return await achievement_service.create_achievement(body)


@router.get(
    "",
    response_model=list[AchievementResponse],
    summary="List all achievements",
)
async def list_achievements() -> list[AchievementResponse]:
    """Return all achievements for the current user."""
    return await achievement_service.list_achievements()


@router.get(
    "/{achievement_id}",
    response_model=AchievementResponse,
    summary="Get achievement detail",
)
async def get_achievement(
    achievement_id: uuid.UUID = Path(..., description="The achievement UUID"),
) -> AchievementResponse:
    """Retrieve a single achievement by its ID."""
    achievement = await achievement_service.get_achievement(achievement_id)
    if achievement is None:
        raise HTTPException(status_code=404, detail="Achievement not found")
    return achievement


@router.post(
    "/{achievement_id}/analyze",
    response_model=AchievementResponse,
    summary="Trigger AI analysis on an achievement",
)
async def analyze_achievement(
    achievement_id: uuid.UUID = Path(..., description="The achievement UUID"),
) -> AchievementResponse:
    """Trigger the AI agent to analyze an achievement and enrich it with parsed data."""
    result = await achievement_service.analyze_achievement(achievement_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Achievement not found")
    return result
