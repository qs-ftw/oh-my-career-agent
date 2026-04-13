"""Database-backed service for achievement operations."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.achievement import Achievement, AchievementRoleMatch
from src.models.agent import AgentRun, UpdateSuggestion
from src.models.gap import GapItem
from src.models.resume import Resume, ResumeVersion
from src.models.story import InterviewStory
from src.models.target_role import RoleCapabilityModel, TargetRole
from src.schemas.achievement import AchievementCreate, AchievementResponse

logger = logging.getLogger(__name__)


def _to_response(a: Achievement) -> AchievementResponse:
    """Convert an Achievement ORM instance to an AchievementResponse schema."""
    return AchievementResponse(
        id=a.id,
        title=a.title,
        raw_content=a.raw_content or "",
        parsed_summary=a.parsed_summary or None,
        technical_points=(
            a.technical_points_json if isinstance(a.technical_points_json, list) else []
        ),
        challenges=(
            a.challenges_json if isinstance(a.challenges_json, list) else []
        ),
        solutions=(
            a.solutions_json if isinstance(a.solutions_json, list) else []
        ),
        metrics=(
            a.metrics_json if isinstance(a.metrics_json, list) else []
        ),
        interview_points=(
            a.interview_points_json
            if isinstance(a.interview_points_json, list) else []
        ),
        tags=a.tags_json if isinstance(a.tags_json, list) else [],
        importance_score=a.importance_score,
        created_at=a.created_at,
    )


async def create_achievement(
    session: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    data: AchievementCreate,
) -> AchievementResponse:
    """Create a new achievement row."""
    achievement = Achievement(
        workspace_id=workspace_id,
        user_id=user_id,
        source_type=data.source_type,
        title=data.title,
        raw_content=data.raw_content,
        tags_json=data.tags or [],
        importance_score=0.0,
    )
    session.add(achievement)
    await session.flush()
    await session.refresh(achievement)
    return _to_response(achievement)


async def list_achievements(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> list[AchievementResponse]:
    """Return all achievements for a user, newest first."""
    stmt = (
        select(Achievement)
        .where(Achievement.user_id == user_id)
        .order_by(Achievement.created_at.desc())
    )
    result = await session.execute(stmt)
    achievements = result.scalars().all()
    return [_to_response(a) for a in achievements]


async def get_achievement(
    session: AsyncSession,
    user_id: uuid.UUID,
    achievement_id: uuid.UUID,
) -> AchievementResponse | None:
    """Return a single achievement by id with ownership check."""
    stmt = select(Achievement).where(
        Achievement.id == achievement_id,
        Achievement.user_id == user_id,
    )
    result = await session.execute(stmt)
    a = result.scalar_one_or_none()
    if a is None:
        return None
    return _to_response(a)


async def run_achievement_pipeline(
    session: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    achievement_id: uuid.UUID,
) -> AchievementResponse | None:
    """Run the achievement analysis pipeline and persist results.

    1. Load the achievement row
    2. Load user's active target roles with capability models, resumes, and gaps
    3. Invoke the LangGraph achievement pipeline
    4. Persist: parsed achievement data, role matches, suggestions, gap updates, agent run
    """
    # 1. Load achievement
    stmt = select(Achievement).where(
        Achievement.id == achievement_id,
        Achievement.user_id == user_id,
    )
    result = await session.execute(stmt)
    achievement = result.scalar_one_or_none()
    if achievement is None:
        return None

    # 2. Load active target roles with related data
    roles_stmt = (
        select(TargetRole)
        .where(
            TargetRole.user_id == user_id,
            TargetRole.deleted_at.is_(None),
            TargetRole.status == "active",
        )
        .order_by(TargetRole.priority.desc())
    )
    roles_result = await session.execute(roles_stmt)
    roles = roles_result.scalars().all()

    target_roles_data = []
    for role in roles:
        # Capability model
        cap_stmt = select(RoleCapabilityModel).where(
            RoleCapabilityModel.target_role_id == role.id
        )
        cap_result = await session.execute(cap_stmt)
        cap = cap_result.scalar_one_or_none()
        cap_model = {}
        if cap:
            cap_model = {
                "core_capabilities": cap.core_capabilities_json or [],
                "secondary_capabilities": cap.secondary_capabilities_json or [],
                "bonus_capabilities": cap.bonus_capabilities_json or [],
                "project_requirements": cap.project_requirements_json or [],
                "evaluation_rules": cap.evaluation_rules_json or [],
            }

        # Master resume content (from latest version)
        resume_stmt = select(Resume).where(
            Resume.target_role_id == role.id,
            Resume.resume_type == "master",
            Resume.deleted_at.is_(None),
        )
        resume_result = await session.execute(resume_stmt)
        resume = resume_result.scalar_one_or_none()

        resume_content = {}
        if resume:
            ver_stmt = (
                select(ResumeVersion)
                .where(ResumeVersion.resume_id == resume.id)
                .order_by(ResumeVersion.version_no.desc())
                .limit(1)
            )
            ver_result = await session.execute(ver_stmt)
            latest_version = ver_result.scalar_one_or_none()
            if latest_version and latest_version.content_json:
                resume_content = (
                    latest_version.content_json
                    if isinstance(latest_version.content_json, dict)
                    else {}
                )

        # Current gaps
        gaps_stmt = select(GapItem).where(
            GapItem.target_role_id == role.id,
            GapItem.status.in_(["open", "in_progress"]),
        )
        gaps_result = await session.execute(gaps_stmt)
        gaps = gaps_result.scalars().all()
        current_gaps = [
            {
                "id": str(g.id),
                "skill_name": g.skill_name,
                "gap_type": g.gap_type,
                "priority": g.priority,
                "progress": g.progress,
                "current_state": g.current_state or "",
                "target_state": g.target_state or "",
            }
            for g in gaps
        ]

        target_roles_data.append({
            "role_id": str(role.id),
            "role_name": role.role_name,
            "role_type": role.role_type,
            "description": role.description or "",
            "required_skills": role.required_skills_json or [],
            "bonus_skills": role.bonus_skills_json or [],
            "capability_model": cap_model,
            "resume_content": resume_content,
            "current_gaps": current_gaps,
        })

    # 3. Build agent input and invoke pipeline
    from src.agent.graph import achievement_graph

    agent_input = {
        "user_id": str(user_id),
        "workspace_id": str(workspace_id),
        "achievement_id": str(achievement_id),
        "achievement_raw": achievement.raw_content or "",
        "target_roles": target_roles_data,
        "achievement_parsed": None,
        "role_matches": [],
        "suggestions": [],
        "gap_updates": [],
        "agent_logs": [],
    }

    try:
        pipeline_result = await achievement_graph.ainvoke(agent_input)
    except Exception as e:
        logger.error(f"Achievement pipeline failed for {achievement_id}: {e}")
        pipeline_result = {
            "achievement_parsed": None,
            "role_matches": [],
            "suggestions": [],
            "gap_updates": [],
            "agent_logs": [{"node": "pipeline", "error": str(e)}],
        }

    # 4. Persist results
    # 4a. Update achievement with parsed data
    parsed = pipeline_result.get("achievement_parsed")
    if parsed:
        achievement.parsed_summary = parsed.get("summary")
        achievement.technical_points_json = parsed.get("technical_points", [])
        achievement.challenges_json = parsed.get("challenges", [])
        achievement.solutions_json = parsed.get("solutions", [])
        achievement.metrics_json = parsed.get("metrics", [])
        achievement.interview_points_json = parsed.get("interview_points", [])
        achievement.tags_json = parsed.get("tags", [])
        achievement.importance_score = float(parsed.get("importance_score", 0.0))

    # 4b. Create role matches
    for match in pipeline_result.get("role_matches", []):
        role_id = match.get("role_id")
        if not role_id:
            continue
        try:
            role_match = AchievementRoleMatch(
                achievement_id=achievement_id,
                target_role_id=uuid.UUID(role_id),
                match_score=float(match.get("match_score", 0.0)),
                match_reason=match.get("reason"),
            )
            session.add(role_match)
        except (ValueError, TypeError):
            logger.warning(f"Invalid role_id in match: {role_id}")

    # 4c. Create update suggestions
    for suggestion in pipeline_result.get("suggestions", []):
        sug = UpdateSuggestion(
            workspace_id=workspace_id,
            user_id=user_id,
            suggestion_type=suggestion.get("suggestion_type", "resume_update"),
            target_role_id=(
                uuid.UUID(suggestion["target_role_id"])
                if suggestion.get("target_role_id") else None
            ),
            resume_id=(
                uuid.UUID(suggestion["resume_id"])
                if suggestion.get("resume_id") else None
            ),
            source_type="achievement_pipeline",
            source_ref_id=achievement_id,
            title=suggestion.get("title", "Update suggestion"),
            content_json=suggestion.get("content"),
            impact_score_json={"score": suggestion.get("impact_score", 0.5)},
            risk_level=suggestion.get("risk_level", "low"),
            status="pending",
        )
        session.add(sug)

    # 4d. Update gap items from pipeline
    for gap_update in pipeline_result.get("gap_updates", []):
        action = gap_update.get("action")
        if action == "update_gap" and gap_update.get("gap_id"):
            try:
                gap_stmt = select(GapItem).where(
                    GapItem.id == uuid.UUID(gap_update["gap_id"]),
                    GapItem.user_id == user_id,
                )
                gap_result = await session.execute(gap_stmt)
                gap = gap_result.scalar_one_or_none()
                if gap:
                    if gap_update.get("progress") is not None:
                        gap.progress = float(gap_update["progress"])
                    if gap_update.get("status"):
                        gap.status = gap_update["status"]
                        if gap_update["status"] == "closed":
                            gap.closed_at = datetime.now(UTC)
                    gap.updated_at = datetime.now(UTC)
            except (ValueError, TypeError):
                pass
        elif action == "create_gap":
            for item in gap_update.get("items", []):
                role_id = item.get("role_id") or (
                    pipeline_result.get("role_matches", [{}])[0].get("role_id")
                    if pipeline_result.get("role_matches") else None
                )
                if not role_id:
                    continue
                gap = GapItem(
                    workspace_id=workspace_id,
                    user_id=user_id,
                    target_role_id=uuid.UUID(role_id),
                    skill_name=item.get("skill_name", "Unknown"),
                    gap_type=item.get("gap_type", "weak_evidence"),
                    priority=item.get("priority", 5),
                    current_state=item.get("current_state", ""),
                    target_state=item.get("target_state", ""),
                    evidence_json=item.get("evidence", []),
                    improvement_plan_json=item.get("improvement_plan", {}),
                    progress=0.0,
                    status="open",
                )
                session.add(gap)

    # 4e. Extract and persist interview stories
    story_candidates = pipeline_result.get("story_candidates", [])
    for candidate in story_candidates:
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

    # 4f. Create agent run audit record
    agent_run = AgentRun(
        workspace_id=workspace_id,
        user_id=user_id,
        run_type="achievement_pipeline",
        source_type="achievement",
        source_ref_id=achievement_id,
        input_payload_json={"achievement_raw": achievement.raw_content},
        output_payload_json={
            "role_matches": pipeline_result.get("role_matches", []),
            "suggestions_count": len(pipeline_result.get("suggestions", [])),
            "gap_updates_count": len(pipeline_result.get("gap_updates", [])),
        },
        status="completed",
    )
    session.add(agent_run)

    achievement.updated_at = datetime.now(UTC)
    await session.flush()
    await session.refresh(achievement)
    return _to_response(achievement)
