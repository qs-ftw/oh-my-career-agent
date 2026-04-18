"""Dashboard aggregation service."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.achievement import Achievement
from src.models.agent import UpdateSuggestion
from src.models.gap import GapItem
from src.models.jd import JDResumeTask
from src.models.profile import CareerProfile
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

    # Recent achievements (JOIN through CareerProfile since Achievement has no user_id)
    recent_achievement_count = await session.scalar(
        select(func.count(Achievement.id))
        .join(CareerProfile, Achievement.profile_id == CareerProfile.id)
        .where(
            CareerProfile.user_id == user_id,
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


async def get_role_summaries(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> list[dict]:
    """Get summary data for each active/paused role for dashboard cards."""
    stmt = (
        select(TargetRole)
        .where(
            TargetRole.user_id == user_id,
            TargetRole.deleted_at.is_(None),
            TargetRole.status.in_(["active", "paused"]),
        )
        .order_by(TargetRole.priority.desc())
    )
    result = await session.execute(stmt)
    roles = result.scalars().all()

    summaries = []
    for role in roles:
        resume = await session.scalar(
            select(Resume).where(
                Resume.target_role_id == role.id,
                Resume.deleted_at.is_(None),
            )
        )
        gap_count = await session.scalar(
            select(func.count(GapItem.id)).where(
                GapItem.target_role_id == role.id,
                GapItem.status.in_(["open", "in_progress"]),
            )
        ) or 0

        summaries.append({
            "id": str(role.id),
            "role_name": role.role_name,
            "role_type": role.role_type,
            "status": role.status,
            "priority": role.priority,
            "completeness_score": resume.completeness_score if resume else 0,
            "match_score": resume.match_score if resume else 0,
            "gap_count": gap_count,
            "updated_at": role.updated_at.isoformat() if role.updated_at else None,
        })
    return summaries


async def get_high_priority_gaps(
    session: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 5,
) -> list[dict]:
    """Get top high-priority open gaps with suggested actions."""
    stmt = (
        select(GapItem)
        .where(
            GapItem.user_id == user_id,
            GapItem.status.in_(["open", "in_progress"]),
        )
        .order_by(GapItem.priority.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    gaps = result.scalars().all()

    return [
        {
            "id": str(g.id),
            "skill_name": g.skill_name,
            "gap_type": g.gap_type,
            "priority": g.priority,
            "status": g.status,
            "progress": g.progress,
            "target_role_id": str(g.target_role_id),
        }
        for g in gaps
    ]
