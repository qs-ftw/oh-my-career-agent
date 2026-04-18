"""Achievement endpoints — database-backed CRUD + AI analysis."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user_id, get_current_workspace_id
from src.schemas.achievement import AchievementCreate, AchievementResponse, AchievementUpdate
from src.services import achievement_service

router = APIRouter(prefix="/achievements", tags=["achievements"])


@router.post(
    "",
    response_model=AchievementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new achievement",
)
async def create_achievement(
    body: AchievementCreate,
    db: AsyncSession = Depends(get_db),
) -> AchievementResponse:
    """Submit a new raw achievement for processing."""
    user_id = await get_current_user_id()
    workspace_id = await get_current_workspace_id()
    return await achievement_service.create_achievement(db, user_id, workspace_id, body)


@router.get(
    "",
    response_model=list[AchievementResponse],
    summary="List all achievements",
)
async def list_achievements(
    db: AsyncSession = Depends(get_db),
) -> list[AchievementResponse]:
    """Return all achievements for the current user."""
    user_id = await get_current_user_id()
    return await achievement_service.list_achievements(db, user_id)


@router.get(
    "/{achievement_id}",
    response_model=AchievementResponse,
    summary="Get achievement detail",
)
async def get_achievement(
    achievement_id: uuid.UUID = Path(..., description="The achievement UUID"),
    db: AsyncSession = Depends(get_db),
) -> AchievementResponse:
    """Retrieve a single achievement by its ID."""
    user_id = await get_current_user_id()
    achievement = await achievement_service.get_achievement(db, user_id, achievement_id)
    if achievement is None:
        raise HTTPException(status_code=404, detail="Achievement not found")
    return achievement


@router.patch(
    "/{achievement_id}",
    response_model=AchievementResponse,
    summary="Update an achievement",
)
async def update_achievement(
    body: AchievementUpdate,
    achievement_id: uuid.UUID = Path(..., description="The achievement UUID"),
    db: AsyncSession = Depends(get_db),
) -> AchievementResponse:
    """Update achievement fields. Supports reassigning to a project."""
    user_id = await get_current_user_id()
    result = await achievement_service.update_achievement(db, user_id, achievement_id, body)
    if result is None:
        raise HTTPException(status_code=404, detail="Achievement not found")
    return result


@router.delete(
    "/{achievement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an achievement",
)
async def delete_achievement(
    achievement_id: uuid.UUID = Path(..., description="The achievement UUID"),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Permanently delete an achievement."""
    user_id = await get_current_user_id()
    deleted = await achievement_service.delete_achievement(db, user_id, achievement_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Achievement not found")


@router.post(
    "/{achievement_id}/analyze",
    response_model=AchievementResponse,
    summary="Trigger AI analysis on an achievement",
)
async def analyze_achievement(
    achievement_id: uuid.UUID = Path(..., description="The achievement UUID"),
    db: AsyncSession = Depends(get_db),
) -> AchievementResponse:
    """Trigger the AI agent to analyze an achievement and enrich it with parsed data.

    This runs the full achievement pipeline: analysis → role matching →
    resume update suggestions → gap evaluation. May take 10-30 seconds.
    """
    user_id = await get_current_user_id()
    workspace_id = await get_current_workspace_id()
    result = await achievement_service.run_achievement_pipeline(
        db, user_id, workspace_id, achievement_id
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Achievement not found")
    return result
