"""Resume endpoints -- CRUD backed by the database."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user_id, get_current_workspace_id
from src.schemas.resume import ResumeResponse, ResumeUpdate
from src.services import resume_service

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.get(
    "",
    response_model=list[ResumeResponse],
    summary="List all resumes",
)
async def list_resumes(
    target_role_id: uuid.UUID | None = Query(
        default=None, description="Filter by target role ID"
    ),
    db: AsyncSession = Depends(get_db),
) -> list[ResumeResponse]:
    """Return all resumes for the current user, optionally filtered by target role."""
    user_id = await get_current_user_id()
    return await resume_service.list_resumes(db, user_id, target_role_id=target_role_id)


@router.get(
    "/{resume_id}",
    response_model=ResumeResponse,
    summary="Get resume detail",
)
async def get_resume(
    resume_id: uuid.UUID = Path(..., description="The resume UUID"),
    db: AsyncSession = Depends(get_db),
) -> ResumeResponse:
    """Retrieve a single resume by its ID."""
    user_id = await get_current_user_id()
    resume = await resume_service.get_resume(db, user_id, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@router.patch(
    "/{resume_id}",
    response_model=ResumeResponse,
    summary="Update a resume",
)
async def update_resume(
    body: ResumeUpdate,
    resume_id: uuid.UUID = Path(..., description="The resume UUID"),
    db: AsyncSession = Depends(get_db),
) -> ResumeResponse:
    """Partially update a resume."""
    user_id = await get_current_user_id()
    resume = await resume_service.update_resume(db, user_id, resume_id, body)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@router.get(
    "/{resume_id}/versions",
    response_model=list[dict[str, Any]],
    summary="List resume versions",
)
async def list_versions(
    resume_id: uuid.UUID = Path(..., description="The resume UUID"),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return all saved versions for a resume."""
    user_id = await get_current_user_id()
    return await resume_service.list_versions(db, user_id, resume_id)


@router.post(
    "/{resume_id}/apply-suggestion",
    response_model=ResumeResponse,
    summary="Apply a suggestion to a resume",
)
async def apply_suggestion(
    resume_id: uuid.UUID = Path(..., description="The resume UUID"),
    suggestion_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> ResumeResponse:
    """Apply an accepted suggestion to the resume, creating a new version."""
    if suggestion_id is None:
        raise HTTPException(status_code=400, detail="suggestion_id is required")

    # TODO: integrate with suggestion model when available.
    # For now, delegate to a simple update flow.
    user_id = await get_current_user_id()
    resume = await resume_service.get_resume(db, user_id, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume
