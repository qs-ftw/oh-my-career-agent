"""Database-backed service for work experience CRUD."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.work_experience import WorkExperience
from src.schemas.work_experience import (
    WorkExperienceCreate,
    WorkExperienceResponse,
    WorkExperienceUpdate,
)


def _to_response(w: WorkExperience) -> WorkExperienceResponse:
    return WorkExperienceResponse(
        id=w.id,
        profile_id=w.profile_id,
        company_name=w.company_name,
        company_url=w.company_url,
        location=w.location,
        role_title=w.role_title,
        start_date=w.start_date,
        end_date=w.end_date,
        description=w.description,
        sort_order=w.sort_order,
        created_at=w.created_at,
        updated_at=w.updated_at,
    )


async def list_by_profile(
    session: AsyncSession,
    profile_id: uuid.UUID,
) -> list[WorkExperienceResponse]:
    stmt = (
        select(WorkExperience)
        .where(WorkExperience.profile_id == profile_id)
        .order_by(WorkExperience.sort_order, WorkExperience.start_date.desc())
    )
    result = await session.execute(stmt)
    return [_to_response(w) for w in result.scalars().all()]


async def create(
    session: AsyncSession,
    profile_id: uuid.UUID,
    data: WorkExperienceCreate,
) -> WorkExperienceResponse:
    exp = WorkExperience(profile_id=profile_id, **data.model_dump())
    session.add(exp)
    await session.flush()
    await session.refresh(exp)
    return _to_response(exp)


async def update(
    session: AsyncSession,
    experience_id: uuid.UUID,
    data: WorkExperienceUpdate,
) -> WorkExperienceResponse | None:
    stmt = select(WorkExperience).where(WorkExperience.id == experience_id)
    result = await session.execute(stmt)
    exp = result.scalar_one_or_none()
    if exp is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(exp, field, value)
    await session.flush()
    await session.refresh(exp)
    return _to_response(exp)


async def delete(
    session: AsyncSession,
    experience_id: uuid.UUID,
) -> bool:
    """Delete a work experience and cascade-delete its projects and achievements."""
    from src.models.achievement import Achievement
    from src.models.project import Project
    from src.models.profile import CareerProfile

    stmt = select(WorkExperience).where(WorkExperience.id == experience_id)
    result = await session.execute(stmt)
    exp = result.scalar_one_or_none()
    if exp is None:
        return False

    # Find all projects under this WE
    proj_stmt = select(Project).where(Project.work_experience_id == experience_id)
    proj_result = await session.execute(proj_stmt)
    projects = proj_result.scalars().all()
    project_ids = [p.id for p in projects]

    # Delete achievements linked to these projects
    if project_ids:
        ach_stmt = select(Achievement).where(Achievement.project_id.in_(project_ids))
        ach_result = await session.execute(ach_stmt)
        for ach in ach_result.scalars().all():
            await session.delete(ach)

    # Delete achievements linked directly to this WE (no project)
    we_ach_stmt = select(Achievement).where(
        Achievement.work_experience_id == experience_id,
        Achievement.project_id.is_(None),
    )
    we_ach_result = await session.execute(we_ach_stmt)
    for ach in we_ach_result.scalars().all():
        await session.delete(ach)

    # Delete projects
    for p in projects:
        await session.delete(p)

    # Delete the work experience itself
    await session.delete(exp)
    await session.flush()
    return True
