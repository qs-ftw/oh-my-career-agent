"""Database-backed service for education CRUD."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.education import Education
from src.schemas.education import (
    EducationCreate,
    EducationResponse,
    EducationUpdate,
)


def _to_response(e: Education) -> EducationResponse:
    return EducationResponse(
        id=e.id,
        profile_id=e.profile_id,
        institution_name=e.institution_name,
        institution_url=e.institution_url,
        degree=e.degree,
        field_of_study=e.field_of_study,
        location=e.location,
        start_date=e.start_date,
        end_date=e.end_date,
        gpa=e.gpa,
        description=e.description,
        sort_order=e.sort_order,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )


async def list_by_profile(
    session: AsyncSession,
    profile_id: uuid.UUID,
) -> list[EducationResponse]:
    stmt = (
        select(Education)
        .where(Education.profile_id == profile_id)
        .order_by(Education.sort_order, Education.start_date.desc())
    )
    result = await session.execute(stmt)
    return [_to_response(e) for e in result.scalars().all()]


async def create(
    session: AsyncSession,
    profile_id: uuid.UUID,
    data: EducationCreate,
) -> EducationResponse:
    edu = Education(profile_id=profile_id, **data.model_dump())
    session.add(edu)
    await session.flush()
    await session.refresh(edu)
    return _to_response(edu)


async def update(
    session: AsyncSession,
    education_id: uuid.UUID,
    data: EducationUpdate,
) -> EducationResponse | None:
    stmt = select(Education).where(Education.id == education_id)
    result = await session.execute(stmt)
    edu = result.scalar_one_or_none()
    if edu is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(edu, field, value)
    await session.flush()
    await session.refresh(edu)
    return _to_response(edu)


async def delete(
    session: AsyncSession,
    education_id: uuid.UUID,
) -> bool:
    """Delete an education and cascade-delete its projects and achievements."""
    from src.models.achievement import Achievement
    from src.models.project import Project

    stmt = select(Education).where(Education.id == education_id)
    result = await session.execute(stmt)
    edu = result.scalar_one_or_none()
    if edu is None:
        return False

    # Find all projects under this Education
    proj_stmt = select(Project).where(Project.education_id == education_id)
    proj_result = await session.execute(proj_stmt)
    projects = proj_result.scalars().all()
    project_ids = [p.id for p in projects]

    # Delete achievements linked to these projects
    if project_ids:
        ach_stmt = select(Achievement).where(Achievement.project_id.in_(project_ids))
        ach_result = await session.execute(ach_stmt)
        for ach in ach_result.scalars().all():
            await session.delete(ach)

    # Delete achievements linked directly to this Education (no project)
    edu_ach_stmt = select(Achievement).where(
        Achievement.education_id == education_id,
        Achievement.project_id.is_(None),
    )
    edu_ach_result = await session.execute(edu_ach_stmt)
    for ach in edu_ach_result.scalars().all():
        await session.delete(ach)

    # Delete projects
    for p in projects:
        await session.delete(p)

    # Delete the education itself
    await session.delete(edu)
    await session.flush()
    return True
