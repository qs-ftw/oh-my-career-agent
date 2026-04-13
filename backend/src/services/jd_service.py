"""Database-backed service for JD (job description) operations."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.achievement import Achievement
from src.models.jd import JDResumeTask, JDSnapshot
from src.models.resume import ResumeVersion
from src.models.target_role import TargetRole
from src.schemas.jd import JDParsedResponse, JDTailorResponse
from src.schemas.resume import ResumeContent

logger = logging.getLogger(__name__)


async def parse_jd(
    session: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    raw_jd: str,
) -> JDParsedResponse:
    """Parse raw JD text into structured data using the jd_parsing agent node."""
    from src.agent.nodes.jd_parsing import jd_parsing

    # Create snapshot
    snapshot = JDSnapshot(
        workspace_id=workspace_id,
        user_id=user_id,
        source_type="manual",
        raw_jd=raw_jd,
    )
    session.add(snapshot)
    await session.flush()

    # Invoke jd_parsing node directly
    state = {
        "jd_raw": raw_jd,
        "agent_logs": [],
    }
    result = await jd_parsing(state)
    parsed = result.get("jd_parsed", {})

    # Update snapshot with parsed data
    snapshot.parsed_role_name = parsed.get("role_name", "")
    snapshot.parsed_keywords_json = parsed.get("keywords", [])
    snapshot.parsed_required_skills_json = parsed.get("required_skills", [])
    snapshot.parsed_bonus_items_json = parsed.get("bonus_items", [])
    snapshot.parsed_style_json = parsed.get("style", {})
    await session.flush()

    return JDParsedResponse(
        role_name=parsed.get("role_name", ""),
        keywords=parsed.get("keywords", []),
        required_skills=parsed.get("required_skills", []),
        bonus_items=parsed.get("bonus_items", []),
        style=parsed.get("style", {}),
    )


async def tailor_jd(
    session: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    raw_jd: str,
    mode: str,
    base_resume_id: uuid.UUID | None = None,
) -> JDTailorResponse:
    """Generate a tailored resume for a given JD using the full pipeline."""
    from src.agent.graph import jd_tailoring_graph

    # 1. Create JD snapshot
    snapshot = JDSnapshot(
        workspace_id=workspace_id,
        user_id=user_id,
        source_type="manual",
        raw_jd=raw_jd,
    )
    session.add(snapshot)
    await session.flush()

    # 2. Create JD resume task
    task = JDResumeTask(
        workspace_id=workspace_id,
        user_id=user_id,
        jd_snapshot_id=snapshot.id,
        mode=mode,
        base_resume_id=base_resume_id,
        status="running",
    )
    session.add(task)
    await session.flush()

    # 3. Load career assets
    # Achievements
    ach_stmt = select(Achievement).where(
        Achievement.user_id == user_id,
        Achievement.importance_score > 0,
    ).order_by(Achievement.importance_score.desc())
    ach_result = await session.execute(ach_stmt)
    achievements = [
        {
            "title": a.title,
            "summary": a.parsed_summary or "",
            "tags": a.tags_json if isinstance(a.tags_json, list) else [],
            "metrics": a.metrics_json if isinstance(a.metrics_json, list) else [],
        }
        for a in ach_result.scalars().all()[:10]
    ]

    # Active roles with skills
    roles_stmt = select(TargetRole).where(
        TargetRole.user_id == user_id,
        TargetRole.deleted_at.is_(None),
        TargetRole.status == "active",
    )
    roles_result = await session.execute(roles_stmt)
    roles = [
        {
            "role_name": r.role_name,
            "required_skills": r.required_skills_json or [],
        }
        for r in roles_result.scalars().all()
    ]

    career_assets = {
        "achievements": achievements,
        "roles": roles,
    }

    # Load candidate profile context
    from src.services.profile_service import get_profile_context
    profile_ctx = await get_profile_context(session, user_id, workspace_id)

    # Load base resume content if tuning
    base_resume_content = None
    if mode == "tune_existing" and base_resume_id:
        ver_stmt = (
            select(ResumeVersion)
            .where(ResumeVersion.resume_id == base_resume_id)
            .order_by(ResumeVersion.version_no.desc())
            .limit(1)
        )
        ver_result = await session.execute(ver_stmt)
        version = ver_result.scalar_one_or_none()
        if version and version.content_json:
            base_resume_content = (
                version.content_json
                if isinstance(version.content_json, dict) else {}
            )

    # 4. Build agent input and invoke pipeline
    agent_input = {
        "user_id": str(user_id),
        "workspace_id": str(workspace_id),
        "candidate_profile": profile_ctx or None,
        "jd_raw": raw_jd,
        "jd_mode": mode,
        "base_resume_id": str(base_resume_id) if base_resume_id else None,
        "career_assets": career_assets,
        "base_resume_content": base_resume_content,
        "jd_parsed": None,
        "resume_draft": None,
        "match_scores": None,
        "suggestions": [],
        "gap_updates": [],
        "agent_logs": [],
    }

    try:
        pipeline_result = await jd_tailoring_graph.ainvoke(agent_input)
    except Exception as e:
        logger.error(f"JD tailoring pipeline failed for task {task.id}: {e}")
        pipeline_result = {
            "jd_parsed": {},
            "resume_draft": {
                "summary": "Failed to generate resume.",
                "skills": [], "experiences": [],
                "projects": [], "highlights": [],
                "metrics": [], "interview_points": [],
            },
            "match_scores": {
                "ability_match_score": 0.0,
                "resume_match_score": 0.0,
                "readiness_score": 0.0,
                "recommendation": "not_recommended",
                "missing_items": [],
                "optimization_notes": [],
            },
            "agent_logs": [{"node": "pipeline", "error": str(e)}],
        }

    # 5. Persist results
    match_scores = pipeline_result.get("match_scores") or {}
    resume_draft = pipeline_result.get("resume_draft") or {}

    task.ability_match_score = match_scores.get("ability_match_score", 0.0)
    task.resume_match_score = match_scores.get("resume_match_score", 0.0)
    task.readiness_score = match_scores.get("readiness_score", 0.0)
    task.recommendation = match_scores.get("recommendation", "not_recommended")
    task.missing_items_json = match_scores.get("missing_items", [])
    task.optimization_notes_json = match_scores.get("optimization_notes", [])
    task.status = "completed"

    # Also update snapshot with parsed data if available
    jd_parsed = pipeline_result.get("jd_parsed") or {}
    if jd_parsed:
        snapshot.parsed_role_name = jd_parsed.get("role_name", "")
        snapshot.parsed_keywords_json = jd_parsed.get("keywords", [])
        snapshot.parsed_required_skills_json = jd_parsed.get("required_skills", [])
        snapshot.parsed_bonus_items_json = jd_parsed.get("bonus_items", [])
        snapshot.parsed_style_json = jd_parsed.get("style", {})

    await session.flush()

    # 6. Build response
    resume_content = (
        ResumeContent(**resume_draft)
        if isinstance(resume_draft, dict) else ResumeContent()
    )

    return JDTailorResponse(
        resume=resume_content,
        ability_match_score=task.ability_match_score,
        resume_match_score=task.resume_match_score,
        readiness_score=task.readiness_score,
        recommendation=match_scores.get("recommendation", "not_recommended"),
        missing_items=(
            match_scores.get("missing_items", [])
            if isinstance(match_scores.get("missing_items"), list) else []
        ),
        optimization_notes=(
            match_scores.get("optimization_notes", [])
            if isinstance(match_scores.get("optimization_notes"), list) else []
        ),
    )


async def get_task(
    session: AsyncSession,
    user_id: uuid.UUID,
    task_id: uuid.UUID,
) -> dict | None:
    """Retrieve the result of a JD processing task."""
    stmt = select(JDResumeTask).where(
        JDResumeTask.id == task_id,
        JDResumeTask.user_id == user_id,
    )
    result = await session.execute(stmt)
    task = result.scalar_one_or_none()
    if task is None:
        return None

    return {
        "task_id": str(task.id),
        "status": task.status,
        "mode": task.mode,
        "ability_match_score": task.ability_match_score,
        "resume_match_score": task.resume_match_score,
        "readiness_score": task.readiness_score,
        "recommendation": task.recommendation,
        "missing_items": task.missing_items_json or [],
        "optimization_notes": task.optimization_notes_json or [],
    }
