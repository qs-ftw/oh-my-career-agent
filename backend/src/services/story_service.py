"""Database-backed service for interview story operations."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.story import InterviewStory
from src.schemas.story import StoryCreate, StoryResponse, StoryUpdate

logger = logging.getLogger(__name__)


def _to_response(story: InterviewStory) -> StoryResponse:
    return StoryResponse(
        id=story.id,
        title=story.title,
        theme=story.theme,
        source_type=story.source_type,
        source_ref_id=story.source_ref_id,
        story_json=story.story_json or {},
        best_for_json=story.best_for_json or [],
        confidence_score=story.confidence_score,
        created_at=story.created_at,
        updated_at=story.updated_at,
    )


async def list_stories(
    session: AsyncSession,
    user_id: uuid.UUID,
    theme: str | None = None,
    source_type: str | None = None,
) -> list[StoryResponse]:
    stmt = (
        select(InterviewStory)
        .where(InterviewStory.user_id == user_id, InterviewStory.deleted_at.is_(None))
        .order_by(InterviewStory.confidence_score.desc(), InterviewStory.created_at.desc())
    )
    if theme is not None:
        stmt = stmt.where(InterviewStory.theme == theme)
    if source_type is not None:
        stmt = stmt.where(InterviewStory.source_type == source_type)

    result = await session.execute(stmt)
    stories = result.scalars().all()
    return [_to_response(s) for s in stories]


async def get_story(
    session: AsyncSession,
    user_id: uuid.UUID,
    story_id: uuid.UUID,
) -> StoryResponse | None:
    stmt = select(InterviewStory).where(
        InterviewStory.id == story_id,
        InterviewStory.user_id == user_id,
        InterviewStory.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    story = result.scalar_one_or_none()
    if story is None:
        return None
    return _to_response(story)


async def create_story(
    session: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    data: StoryCreate,
) -> StoryResponse:
    story = InterviewStory(
        workspace_id=workspace_id,
        user_id=user_id,
        title=data.title,
        theme=data.theme,
        source_type=data.source_type,
        source_ref_id=data.source_ref_id,
        story_json=data.story_json,
        best_for_json=data.best_for_json,
        confidence_score=data.confidence_score,
    )
    session.add(story)
    await session.flush()
    await session.refresh(story)
    return _to_response(story)


async def update_story(
    session: AsyncSession,
    user_id: uuid.UUID,
    story_id: uuid.UUID,
    data: StoryUpdate,
) -> StoryResponse | None:
    stmt = select(InterviewStory).where(
        InterviewStory.id == story_id,
        InterviewStory.user_id == user_id,
        InterviewStory.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    story = result.scalar_one_or_none()
    if story is None:
        return None

    update_map = data.model_dump(exclude_unset=True)
    if "title" in update_map:
        story.title = update_map["title"]
    if "theme" in update_map:
        story.theme = update_map["theme"]
    if "story_json" in update_map:
        story.story_json = update_map["story_json"]
    if "best_for_json" in update_map:
        story.best_for_json = update_map["best_for_json"]
    if "confidence_score" in update_map:
        story.confidence_score = update_map["confidence_score"]

    await session.flush()
    await session.refresh(story)
    return _to_response(story)


async def rebuild_from_achievement(
    session: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    achievement_id: uuid.UUID,
) -> list[StoryResponse]:
    """Extract STAR stories from an achievement and persist them.

    Uses the story_extraction agent node to generate story candidates
    from the achievement's parsed data.
    """
    from src.models.achievement import Achievement

    # Load the achievement
    stmt = select(Achievement).where(Achievement.id == achievement_id)
    result = await session.execute(stmt)
    achievement = result.scalar_one_or_none()
    if achievement is None:
        return []

    # Build parsed data for story extraction
    achievement_parsed = {
        "title": achievement.title,
        "summary": achievement.parsed_summary or "",
        "technical_points": achievement.technical_points_json or [],
        "challenges": achievement.challenges_json or [],
        "solutions": achievement.solutions_json or [],
        "metrics": achievement.metrics_json or [],
        "interview_points": achievement.interview_points_json or [],
        "tags": achievement.tags_json or [],
    }

    # Invoke story extraction node
    try:
        from src.agent.nodes.story_extraction import story_extraction
        state = {
            "achievement_parsed": achievement_parsed,
            "achievement_id": str(achievement_id),
            "agent_logs": [],
        }
        result_state = await story_extraction(state)
        candidates = result_state.get("story_candidates", [])
    except Exception as e:
        logger.error(f"Story extraction failed for achievement {achievement_id}: {e}")
        # Fallback: create a basic story from interview points
        candidates = []
        if achievement_parsed.get("interview_points"):
            candidates.append({
                "title": f"{achievement.title} - 面试故事",
                "theme": "general",
                "story_json": {
                    "situation": achievement_parsed.get("summary", ""),
                    "task": "",
                    "action": ", ".join(str(p) for p in achievement_parsed.get("technical_points", [])[:3]),
                    "result": ", ".join(str(m) for m in achievement_parsed.get("metrics", [])[:3]),
                },
                "best_for": achievement_parsed.get("tags", [])[:5],
                "confidence_score": 0.5,
            })

    # Persist stories
    created = []
    for candidate in candidates:
        story = InterviewStory(
            workspace_id=workspace_id,
            user_id=user_id,
            title=candidate.get("title", achievement.title),
            theme=candidate.get("theme", "general"),
            source_type="achievement",
            source_ref_id=achievement_id,
            story_json=candidate.get("story_json", {}),
            best_for_json=candidate.get("best_for", []),
            confidence_score=candidate.get("confidence_score", 0.0),
        )
        session.add(story)
        await session.flush()
        await session.refresh(story)
        created.append(_to_response(story))

    return created
