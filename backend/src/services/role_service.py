"""Database-backed service for target role CRUD operations."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.achievement import Achievement
from src.models.target_role import RoleCapabilityModel, TargetRole
from src.schemas.role import RoleCreate, RoleResponse, RoleUpdate

logger = logging.getLogger(__name__)


def _to_response(role: TargetRole) -> RoleResponse:
    """Convert a TargetRole ORM instance to a RoleResponse schema."""
    return RoleResponse(
        id=role.id,
        role_name=role.role_name,
        role_type=role.role_type,
        description=role.description or "",
        keywords=role.keywords_json or [],
        required_skills=role.required_skills_json or [],
        bonus_skills=role.bonus_skills_json or [],
        priority=role.priority,
        status=role.status,
        created_at=role.created_at,
        updated_at=role.updated_at,
    )


async def create_role(
    session: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    data: RoleCreate,
) -> RoleResponse:
    """Create a new target role with a placeholder capability row."""
    role = TargetRole(
        workspace_id=workspace_id,
        user_id=user_id,
        role_name=data.role_name,
        role_type=data.role_type,
        description=data.description or None,
        keywords_json=data.keywords,
        required_skills_json=data.required_skills,
        bonus_skills_json=data.bonus_skills,
        priority=data.priority,
        status="active",
        source_jd_summary=data.source_jd,
    )
    session.add(role)
    await session.flush()

    capability = RoleCapabilityModel(
        target_role_id=role.id,
    )
    session.add(capability)
    await session.flush()
    await session.refresh(role)
    return _to_response(role)


async def initialize_role_assets(
    session: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    role_id: uuid.UUID,
    data: RoleCreate,
) -> None:
    """Run the role initialization agent pipeline and persist results.

    After creating a role, this:
    1. Runs the LangGraph role_init pipeline (capability model + resume + gaps)
    2. Updates the capability model in DB
    3. Creates the master resume with generated skeleton
    4. Creates initial gap items
    """
    from src.agent.graph import role_init_graph
    from src.models.resume import Resume
    from src.services.resume_service import create_resume_for_role

    # Soft-delete any existing resumes for this role so regeneration works
    existing_stmt = select(Resume).where(
        Resume.target_role_id == role_id,
        Resume.deleted_at.is_(None),
    )
    existing_result = await session.execute(existing_stmt)
    for old_resume in existing_result.scalars().all():
        old_resume.deleted_at = datetime.now(UTC)
    await session.flush()

    # Load user achievements for resume generation
    ach_stmt = (
        select(Achievement)
        .where(
            Achievement.user_id == user_id,
            Achievement.importance_score > 0,
        )
        .order_by(Achievement.importance_score.desc())
    )
    ach_result = await session.execute(ach_stmt)
    achievements = [
        {
            "title": a.title,
            "summary": a.parsed_summary or "",
            "tags": a.tags_json if isinstance(a.tags_json, list) else [],
            "metrics": a.metrics_json if isinstance(a.metrics_json, list) else [],
            "raw_content": a.raw_content or "",
        }
        for a in ach_result.scalars().all()[:10]
    ]

    career_assets = {"achievements": achievements}

    # Load candidate profile context
    from src.services.profile_service import get_profile_context
    profile_ctx = await get_profile_context(session, user_id, workspace_id)

    # Build agent state from role input
    agent_input = {
        "user_id": str(user_id),
        "workspace_id": str(workspace_id),
        "candidate_profile": profile_ctx or None,
        "target_role_input": {
            "role_name": data.role_name,
            "role_type": data.role_type,
            "description": data.description,
            "required_skills": data.required_skills,
            "bonus_skills": data.bonus_skills,
            "keywords": data.keywords,
            "source_jd": data.source_jd,
        },
        "career_assets": career_assets,
        "suggestions": [],
        "gap_updates": [],
        "agent_logs": [],
    }

    # Run the pipeline
    try:
        result = await role_init_graph.ainvoke(agent_input)
    except Exception as e:
        logger.error(f"Role init pipeline failed for {role_id}: {e}")
        # Create a basic resume even if agent fails
        result = {
            "capability_model": None,
            "resume_draft": {
                "summary": f"Experienced {data.role_name}.",
                "skills": data.required_skills or [],
                "experiences": [],
                "projects": [],
                "highlights": [],
                "metrics": [],
                "interview_points": [],
            },
            "gap_updates": [],
        }

    # 1. Update capability model
    capability_model = result.get("capability_model")
    if capability_model:
        stmt = select(RoleCapabilityModel).where(
            RoleCapabilityModel.target_role_id == role_id
        )
        cap_result = await session.execute(stmt)
        cap = cap_result.scalar_one_or_none()
        if cap:
            cap.core_capabilities_json = capability_model.get("core_capabilities")
            cap.secondary_capabilities_json = capability_model.get("secondary_capabilities")
            cap.bonus_capabilities_json = capability_model.get("bonus_capabilities")
            cap.project_requirements_json = capability_model.get("project_requirements")
            cap.evaluation_rules_json = capability_model.get("evaluation_rules")
            await session.flush()

    # 2. Create master resume with generated content
    resume_draft = result.get("resume_draft")
    if resume_draft:
        await create_resume_for_role(
            session,
            user_id,
            workspace_id,
            role_id,
            resume_draft,
            role_skills=data.required_skills or [],
        )

    # 3. Create initial gap items
    from src.models.gap import GapItem

    for gap_update in result.get("gap_updates", []):
        for item in gap_update.get("items", []):
            gap = GapItem(
                workspace_id=workspace_id,
                user_id=user_id,
                target_role_id=role_id,
                skill_name=item.get("skill_name", "Unknown"),
                gap_type=item.get("gap_type", "weak_evidence"),
                priority=item.get("priority", 5),
                current_state=item.get("current_state", ""),
                target_state=item.get("target_state", ""),
                evidence_json={},
                improvement_plan_json=item.get("improvement_plan", {}),
                progress=0,
                status="open",
            )
            session.add(gap)

    await session.flush()
    logger.info(f"Role assets initialized for {role_id}")


async def list_roles(
    session: AsyncSession,
    user_id: uuid.UUID,
    status_filter: str | None = None,
) -> list[RoleResponse]:
    """Return all non-deleted roles for *user_id*, optionally filtered by status."""
    stmt = (
        select(TargetRole)
        .where(TargetRole.user_id == user_id, TargetRole.deleted_at.is_(None))
        .order_by(TargetRole.priority.desc(), TargetRole.created_at.desc())
    )
    if status_filter is not None:
        stmt = stmt.where(TargetRole.status == status_filter)

    result = await session.execute(stmt)
    roles = result.scalars().all()
    return [_to_response(r) for r in roles]


async def get_role(
    session: AsyncSession,
    user_id: uuid.UUID,
    role_id: uuid.UUID,
) -> RoleResponse | None:
    """Return a single role by id (must belong to *user_id* and not be deleted)."""
    stmt = select(TargetRole).where(
        TargetRole.id == role_id,
        TargetRole.user_id == user_id,
        TargetRole.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    role = result.scalar_one_or_none()
    if role is None:
        return None
    return _to_response(role)


async def update_role(
    session: AsyncSession,
    user_id: uuid.UUID,
    role_id: uuid.UUID,
    data: RoleUpdate,
) -> RoleResponse | None:
    """Patch-update a target role. Only fields that are not None are changed."""
    stmt = select(TargetRole).where(
        TargetRole.id == role_id,
        TargetRole.user_id == user_id,
        TargetRole.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    role = result.scalar_one_or_none()
    if role is None:
        return None

    update_map = data.model_dump(exclude_unset=True)

    if "role_name" in update_map:
        role.role_name = update_map["role_name"]
    if "role_type" in update_map:
        role.role_type = update_map["role_type"]
    if "description" in update_map:
        role.description = update_map["description"]
    if "keywords" in update_map:
        role.keywords_json = update_map["keywords"]
    if "required_skills" in update_map:
        role.required_skills_json = update_map["required_skills"]
    if "bonus_skills" in update_map:
        role.bonus_skills_json = update_map["bonus_skills"]
    if "priority" in update_map:
        role.priority = update_map["priority"]
    if "source_jd" in update_map:
        role.source_jd_summary = update_map["source_jd"]
    if "status" in update_map:
        role.status = update_map["status"]

    role.updated_at = datetime.now(UTC)

    await session.flush()
    await session.refresh(role)
    return _to_response(role)


async def delete_role(
    session: AsyncSession,
    user_id: uuid.UUID,
    role_id: uuid.UUID,
) -> bool:
    """Soft-delete a target role. Returns True if the row was found, False otherwise."""
    stmt = select(TargetRole).where(
        TargetRole.id == role_id,
        TargetRole.user_id == user_id,
        TargetRole.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    role = result.scalar_one_or_none()
    if role is None:
        return False

    role.deleted_at = datetime.now(UTC)
    role.status = "deleted"

    await session.flush()
    return True
