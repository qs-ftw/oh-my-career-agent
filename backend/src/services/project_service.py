"""Database-backed service for project CRUD."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.project import Project
from src.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate


def _to_response(p: Project) -> ProjectResponse:
    return ProjectResponse(
        id=p.id,
        profile_id=p.profile_id,
        work_experience_id=p.work_experience_id,
        education_id=p.education_id,
        name=p.name,
        description=p.description,
        tech_stack=p.tech_stack or [],
        url=p.url,
        start_date=p.start_date,
        end_date=p.end_date,
        sort_order=p.sort_order,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


async def list_by_profile(
    session: AsyncSession,
    profile_id: uuid.UUID,
) -> list[ProjectResponse]:
    stmt = (
        select(Project)
        .where(Project.profile_id == profile_id)
        .order_by(Project.sort_order, Project.created_at.desc())
    )
    result = await session.execute(stmt)
    return [_to_response(p) for p in result.scalars().all()]


async def create(
    session: AsyncSession,
    profile_id: uuid.UUID,
    data: ProjectCreate,
) -> ProjectResponse:
    proj = Project(profile_id=profile_id, **data.model_dump())
    session.add(proj)
    await session.flush()
    await session.refresh(proj)
    return _to_response(proj)


async def update(
    session: AsyncSession,
    project_id: uuid.UUID,
    data: ProjectUpdate,
) -> ProjectResponse | None:
    stmt = select(Project).where(Project.id == project_id)
    result = await session.execute(stmt)
    proj = result.scalar_one_or_none()
    if proj is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(proj, field, value)
    await session.flush()
    await session.refresh(proj)
    return _to_response(proj)


async def delete(
    session: AsyncSession,
    project_id: uuid.UUID,
) -> bool:
    stmt = select(Project).where(Project.id == project_id)
    result = await session.execute(stmt)
    proj = result.scalar_one_or_none()
    if proj is None:
        return False
    await session.delete(proj)
    await session.flush()
    return True
