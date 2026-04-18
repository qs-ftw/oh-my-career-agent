"""Project endpoints — CRUD."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user_id, get_current_workspace_id
from src.models.profile import CareerProfile
from src.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from src.services import project_service

router = APIRouter(prefix="/projects", tags=["projects"])


async def _resolve_profile_id(db: AsyncSession, user_id: uuid.UUID, workspace_id: uuid.UUID) -> uuid.UUID:
    stmt = select(CareerProfile.id).where(
        CareerProfile.user_id == user_id,
        CareerProfile.workspace_id == workspace_id,
    )
    result = await db.execute(stmt)
    profile_id = result.scalar_one_or_none()
    if profile_id is None:
        raise HTTPException(status_code=404, detail="Career profile not found. Create one first.")
    return profile_id


@router.get("", response_model=list[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    user_id = await get_current_user_id()
    workspace_id = await get_current_workspace_id()
    profile_id = await _resolve_profile_id(db, user_id, workspace_id)
    return await project_service.list_by_profile(db, profile_id)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
):
    user_id = await get_current_user_id()
    workspace_id = await get_current_workspace_id()
    profile_id = await _resolve_profile_id(db, user_id, workspace_id)
    return await project_service.create(db, profile_id, body)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID = Path(...),
    body: ProjectUpdate = ...,
    db: AsyncSession = Depends(get_db),
):
    result = await project_service.update(db, project_id, body)
    if result is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return result


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
):
    deleted = await project_service.delete(db, project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
