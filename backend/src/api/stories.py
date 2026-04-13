"""Interview story endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user_id, get_current_workspace_id
from src.schemas.story import StoryListResponse, StoryResponse, StoryUpdate
from src.services import story_service

router = APIRouter(prefix="/stories", tags=["stories"])


@router.get(
    "",
    response_model=StoryListResponse,
    summary="List interview stories",
)
async def list_stories(
    theme: str | None = Query(default=None, description="Filter by theme"),
    source_type: str | None = Query(default=None, description="Filter by source type"),
    db: AsyncSession = Depends(get_db),
) -> StoryListResponse:
    user_id = await get_current_user_id()
    items = await story_service.list_stories(db, user_id, theme=theme, source_type=source_type)
    return StoryListResponse(items=items, total=len(items))


@router.post(
    "/rebuild/{achievement_id}",
    response_model=list[StoryResponse],
    summary="Rebuild stories from an achievement",
)
async def rebuild_stories(
    achievement_id: uuid.UUID = Path(..., description="The achievement UUID"),
    db: AsyncSession = Depends(get_db),
) -> list[StoryResponse]:
    user_id = await get_current_user_id()
    workspace_id = await get_current_workspace_id()
    stories = await story_service.rebuild_from_achievement(
        db, user_id, workspace_id, achievement_id
    )
    return stories


@router.patch(
    "/{story_id}",
    response_model=StoryResponse,
    summary="Update an interview story",
)
async def update_story(
    body: StoryUpdate,
    story_id: uuid.UUID = Path(..., description="The story UUID"),
    db: AsyncSession = Depends(get_db),
) -> StoryResponse:
    user_id = await get_current_user_id()
    story = await story_service.update_story(db, user_id, story_id, body)
    if story is None:
        raise HTTPException(status_code=404, detail="Story not found")
    return story
