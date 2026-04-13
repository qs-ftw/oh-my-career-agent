"""Dashboard aggregation service."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.achievement import Achievement
from src.models.agent import UpdateSuggestion
from src.models.gap import GapItem
from src.models.jd import JDResumeTask
from src.models.resume import Resume
from src.models.story import InterviewStory
from src.models.target_role import TargetRole


async def get_dashboard_stats(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> dict:
    """Aggregate dashboard metrics from the database."""
    # Role count
    role_count = await session.scalar(
        select(func.count(TargetRole.id)).where(
            TargetRole.user_id == user_id,
            TargetRole.deleted_at.is_(None),
            TargetRole.status == "active",
        )
    ) or 0

    # Active resume count
    resume_count = await session.scalar(
        select(func.count(Resume.id)).where(
            Resume.user_id == user_id,
            Resume.deleted_at.is_(None),
        )
    ) or 0

    # Open high-priority gaps
    gap_count = await session.scalar(
        select(func.count(GapItem.id)).where(
            GapItem.user_id == user_id,
            GapItem.status.in_(["open", "in_progress"]),
            GapItem.priority >= 7,
        )
    ) or 0

    # Recent achievements (last 30 days)
    recent_achievement_count = await session.scalar(
        select(func.count(Achievement.id)).where(
            Achievement.user_id == user_id,
            Achievement.importance_score > 0,
        )
    ) or 0

    # Pending suggestions
    pending_suggestion_count = await session.scalar(
        select(func.count(UpdateSuggestion.id)).where(
            UpdateSuggestion.user_id == user_id,
            UpdateSuggestion.status == "pending",
        )
    ) or 0

    # Story count
    story_count = await session.scalar(
        select(func.count(InterviewStory.id)).where(
            InterviewStory.user_id == user_id,
            InterviewStory.deleted_at.is_(None),
        )
    ) or 0

    return {
        "role_count": role_count,
        "resume_count": resume_count,
        "high_priority_gap_count": gap_count,
        "recent_achievement_count": recent_achievement_count,
        "pending_suggestion_count": pending_suggestion_count,
        "story_count": story_count,
    }


async def get_recent_jd_decisions(
    session: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 5,
) -> list[dict]:
    """Get recent JD tailoring decisions."""
    stmt = (
        select(JDResumeTask)
        .where(JDResumeTask.user_id == user_id, JDResumeTask.status == "completed")
        .order_by(JDResumeTask.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    tasks = result.scalars().all()

    return [
        {
            "task_id": str(t.id),
            "recommendation": t.recommendation,
            "ability_match_score": t.ability_match_score,
            "resume_match_score": t.resume_match_score,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tasks
    ]
