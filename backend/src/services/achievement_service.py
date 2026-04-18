"""Database-backed service for achievement operations."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.achievement import Achievement, AchievementRoleMatch
from src.models.profile import CareerProfile
from src.models.agent import AgentRun, UpdateSuggestion
from src.models.gap import GapItem
from src.models.resume import Resume, ResumeVersion
from src.models.story import InterviewStory
from src.models.target_role import RoleCapabilityModel, TargetRole
from src.schemas.achievement import AchievementCreate, AchievementResponse, AchievementUpdate, _UNSET

logger = logging.getLogger(__name__)


def _to_response(a: Achievement, analysis_error: str | None = None) -> AchievementResponse:
    """Convert an Achievement ORM instance to an AchievementResponse schema."""
    return AchievementResponse(
        id=a.id,
        profile_id=a.profile_id,
        project_id=a.project_id,
        work_experience_id=a.work_experience_id,
        education_id=a.education_id,
        title=a.title,
        raw_content=a.raw_content or "",
        parsed_data=a.parsed_data,
        tags=a.tags if isinstance(a.tags, list) else [],
        importance_score=a.importance_score,
        source_type=a.source_type,
        status=a.status,
        date_occurred=a.date_occurred,
        analysis_error=analysis_error,
        analysis_chat=a.analysis_chat,
        enrichment_suggestions=a.enrichment_suggestions,
        polished_content=a.polished_content,
        display_format=a.display_format or "raw",
        created_at=a.created_at,
    )


async def create_achievement(
    session: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    data: AchievementCreate,
) -> AchievementResponse:
    """Create a new achievement row."""
    # Resolve profile_id — auto-create profile if missing
    profile_stmt = select(CareerProfile).where(
        CareerProfile.user_id == user_id,
        CareerProfile.workspace_id == workspace_id,
    )
    profile_result = await session.execute(profile_stmt)
    profile = profile_result.scalar_one_or_none()

    if profile is None:
        profile = CareerProfile(workspace_id=workspace_id, user_id=user_id)
        session.add(profile)
        await session.flush()

    achievement = Achievement(
        profile_id=profile.id,
        project_id=data.project_id,
        work_experience_id=data.work_experience_id,
        title=data.title,
        raw_content=data.raw_content,
        tags=data.tags or [],
        source_type=data.source_type,
        date_occurred=data.date_occurred,
    )
    session.add(achievement)
    await session.flush()
    await session.refresh(achievement)
    return _to_response(achievement)


async def delete_achievement(
    session: AsyncSession,
    user_id: uuid.UUID,
    achievement_id: uuid.UUID,
) -> bool:
    """Delete an achievement and its related data. Returns True if deleted, False if not found."""
    stmt = (
        select(Achievement)
        .join(CareerProfile, Achievement.profile_id == CareerProfile.id)
        .where(
            Achievement.id == achievement_id,
            CareerProfile.user_id == user_id,
        )
    )
    result = await session.execute(stmt)
    achievement = result.scalar_one_or_none()
    if achievement is None:
        return False

    # Delete related records first to avoid FK violations
    from src.models.achievement import AchievementRoleMatch, AchievementResumeLink
    from src.models.agent import UpdateSuggestion

    for Model in (AchievementRoleMatch, AchievementResumeLink):
        rel_stmt = select(Model).where(Model.achievement_id == achievement_id)
        rel_result = await session.execute(rel_stmt)
        for obj in rel_result.scalars().all():
            await session.delete(obj)

    sug_stmt = select(UpdateSuggestion).where(
        UpdateSuggestion.source_achievement_id == achievement_id
    )
    sug_result = await session.execute(sug_stmt)
    for sug in sug_result.scalars().all():
        await session.delete(sug)

    # Flush to ensure related records are deleted before the achievement itself
    await session.flush()

    await session.delete(achievement)
    await session.flush()
    return True


async def list_achievements(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> list[AchievementResponse]:
    """Return all achievements for a user, newest first."""
    stmt = (
        select(Achievement)
        .join(CareerProfile, Achievement.profile_id == CareerProfile.id)
        .where(CareerProfile.user_id == user_id)
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
    stmt = (
        select(Achievement)
        .join(CareerProfile, Achievement.profile_id == CareerProfile.id)
        .where(
            Achievement.id == achievement_id,
            CareerProfile.user_id == user_id,
        )
    )
    result = await session.execute(stmt)
    a = result.scalar_one_or_none()
    if a is None:
        return None
    return _to_response(a)


async def update_achievement(
    session: AsyncSession,
    user_id: uuid.UUID,
    achievement_id: uuid.UUID,
    data: AchievementUpdate,
) -> AchievementResponse | None:
    """Update achievement fields. Returns None if not found or not owned."""
    stmt = (
        select(Achievement)
        .join(CareerProfile, Achievement.profile_id == CareerProfile.id)
        .where(
            Achievement.id == achievement_id,
            CareerProfile.user_id == user_id,
        )
    )
    result = await session.execute(stmt)
    achievement = result.scalar_one_or_none()
    if achievement is None:
        return None

    # Update scalar fields (skip None values)
    if data.title is not None:
        achievement.title = data.title
    if data.raw_content is not None:
        achievement.raw_content = data.raw_content
    if data.tags is not None:
        achievement.tags = data.tags
    if data.display_format is not None:
        achievement.display_format = data.display_format

    # Handle project_id: distinguish _UNSET (not sent) from None (clear) from UUID (set)
    if data.project_id is not _UNSET:
        if data.project_id is None:
            # Explicitly clearing project assignment
            achievement.project_id = None
            # Also clear work_experience_id if not explicitly set
            if data.work_experience_id is _UNSET:
                achievement.work_experience_id = None
        else:
            # Assigning to a project — auto-derive work_experience_id
            achievement.project_id = data.project_id
            from src.models.project import Project
            proj_stmt = select(Project).where(Project.id == data.project_id)
            proj_result = await session.execute(proj_stmt)
            project = proj_result.scalar_one_or_none()
            if project and project.work_experience_id:
                achievement.work_experience_id = project.work_experience_id

    # Handle work_experience_id independently (if explicitly sent)
    if data.work_experience_id is not _UNSET and data.project_id is _UNSET:
        achievement.work_experience_id = data.work_experience_id

    await session.flush()
    await session.refresh(achievement)
    return _to_response(achievement)


async def _build_target_roles_data(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> list[dict]:
    """Load active target roles with related data for agent input."""
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

    return target_roles_data


async def persist_pipeline_results(
    session: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    achievement_id: uuid.UUID,
    pipeline_result: dict,
    target_roles_data: list[dict],
    pipeline_error: str | None = None,
) -> AchievementResponse | None:
    """Persist pipeline results to the database.

    Shared by both the synchronous and streaming analysis paths.
    """
    # Reload achievement
    stmt = (
        select(Achievement)
        .join(CareerProfile, Achievement.profile_id == CareerProfile.id)
        .where(
            Achievement.id == achievement_id,
            CareerProfile.user_id == user_id,
        )
    )
    result = await session.execute(stmt)
    achievement = result.scalar_one_or_none()
    if achievement is None:
        return None

    # Update achievement with parsed data
    achievement.parsed_data = pipeline_result.get("achievement_parsed")
    achievement.importance_score = (
        (pipeline_result.get("achievement_parsed") or {}).get("importance_score", 0.0)
    )
    achievement.status = "analyzed"

    # Create role matches
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

    # Create update suggestions
    role_resume_map: dict[uuid.UUID, uuid.UUID] = {}
    for role_data in target_roles_data:
        rid = role_data.get("role_id")
        if rid:
            try:
                role_uuid = uuid.UUID(rid)
                resume_stmt = select(Resume).where(
                    Resume.target_role_id == role_uuid,
                    Resume.resume_type == "master",
                    Resume.deleted_at.is_(None),
                )
                resume_result = await session.execute(resume_stmt)
                resume = resume_result.scalar_one_or_none()
                if resume:
                    role_resume_map[role_uuid] = resume.id
            except (ValueError, TypeError):
                pass

    for suggestion in pipeline_result.get("suggestions", []):
        try:
            target_role_id_val = (
                uuid.UUID(suggestion["target_role_id"])
                if suggestion.get("target_role_id") else None
            )
        except (ValueError, TypeError, KeyError):
            target_role_id_val = None

        try:
            resume_id_val = (
                uuid.UUID(suggestion["resume_id"])
                if suggestion.get("resume_id") else None
            )
        except (ValueError, TypeError, KeyError):
            resume_id_val = None

        if resume_id_val is None and target_role_id_val in role_resume_map:
            resume_id_val = role_resume_map[target_role_id_val]

        sug = UpdateSuggestion(
            workspace_id=workspace_id,
            user_id=user_id,
            suggestion_type=suggestion.get("suggestion_type", "resume_update"),
            target_role_id=target_role_id_val,
            resume_id=resume_id_val,
            source_type="achievement_pipeline",
            source_ref_id=achievement_id,
            source_achievement_id=achievement_id,
            title=suggestion.get("title", "Update suggestion"),
            content_json=suggestion.get("content"),
            impact_score_json={"score": suggestion.get("impact_score", 0.5)},
            risk_level=suggestion.get("risk_level", "low"),
            status="pending",
        )
        session.add(sug)

    # Update gap items from pipeline
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

    # Extract and persist interview stories
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

    # Create agent run audit record
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
            "pipeline_error": pipeline_error,
        },
        status="failed" if pipeline_error else "completed",
    )
    session.add(agent_run)

    achievement.updated_at = datetime.now(UTC)
    await session.flush()
    await session.refresh(achievement)
    return _to_response(achievement, analysis_error=pipeline_error)


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
    stmt = (
        select(Achievement)
        .join(CareerProfile, Achievement.profile_id == CareerProfile.id)
        .where(
            Achievement.id == achievement_id,
            CareerProfile.user_id == user_id,
        )
    )
    result = await session.execute(stmt)
    achievement = result.scalar_one_or_none()
    if achievement is None:
        return None

    # 2. Load active target roles with related data
    target_roles_data = await _build_target_roles_data(session, user_id)

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

    pipeline_error: str | None = None

    try:
        pipeline_result = await achievement_graph.ainvoke(agent_input)
        pipeline_error = pipeline_result.get("pipeline_error")
        if pipeline_error:
            logger.error(
                f"Achievement pipeline for {achievement_id} completed with errors: {pipeline_error}"
            )
    except Exception as e:
        error_type = type(e).__name__
        logger.error(f"Achievement pipeline crashed for {achievement_id}: {error_type}: {e}")
        pipeline_error = f"Pipeline crashed: {error_type}: {e}"
        pipeline_result = {
            "achievement_parsed": None,
            "role_matches": [],
            "suggestions": [],
            "gap_updates": [],
            "agent_logs": [{"node": "pipeline", "level": "error", "message": str(e)}],
        }

    # 4. Persist results
    return await persist_pipeline_results(
        session=session,
        user_id=user_id,
        workspace_id=workspace_id,
        achievement_id=achievement_id,
        pipeline_result=pipeline_result,
        target_roles_data=target_roles_data,
        pipeline_error=pipeline_error,
    )
