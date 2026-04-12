"""Resume endpoints — stubs returning mock data."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Path, status

from src.schemas.resume import ResumeResponse, ResumeUpdate
from src.services import resume_service

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.get(
    "",
    response_model=list[ResumeResponse],
    summary="List all resumes",
)
async def list_resumes() -> list[ResumeResponse]:
    """Return all resumes for the current user."""
    return await resume_service.list_resumes()


@router.get(
    "/{resume_id}",
    response_model=ResumeResponse,
    summary="Get resume detail",
)
async def get_resume(
    resume_id: uuid.UUID = Path(..., description="The resume UUID"),
) -> ResumeResponse:
    """Retrieve a single resume by its ID."""
    resume = await resume_service.get_resume(resume_id)
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
) -> ResumeResponse:
    """Partially update a resume."""
    resume = await resume_service.update_resume(resume_id, body)
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
) -> list[dict[str, Any]]:
    """Return all saved versions for a resume."""
    return await resume_service.list_versions(resume_id)


@router.post(
    "/{resume_id}/apply-suggestion",
    response_model=ResumeResponse,
    summary="Apply a suggestion to a resume",
)
async def apply_suggestion(
    resume_id: uuid.UUID = Path(..., description="The resume UUID"),
    suggestion_id: uuid.UUID | None = None,
) -> ResumeResponse:
    """Apply an accepted suggestion to the resume, creating a new version."""
    if suggestion_id is None:
        raise HTTPException(status_code=400, detail="suggestion_id is required")
    resume = await resume_service.apply_suggestion(resume_id, suggestion_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume
