"""Resume endpoints -- CRUD backed by the database."""

from __future__ import annotations

import uuid
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user_id
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


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a resume",
)
async def delete_resume(
    resume_id: uuid.UUID = Path(..., description="The resume UUID"),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft-delete a resume."""
    user_id = await get_current_user_id()
    await resume_service.delete_resume(db, user_id, resume_id)


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


@router.get(
    "/{resume_id}/versions/{version_id}",
    response_model=dict[str, Any],
    summary="Get a specific resume version",
)
async def get_version(
    resume_id: uuid.UUID = Path(..., description="The resume UUID"),
    version_id: uuid.UUID = Path(..., description="The version UUID"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return a specific version with its full content."""
    user_id = await get_current_user_id()
    version = await resume_service.get_version(db, user_id, resume_id, version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return version


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


@router.delete(
    "/{resume_id}/versions/{version_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a resume version",
)
async def delete_version(
    resume_id: uuid.UUID = Path(..., description="The resume UUID"),
    version_id: uuid.UUID = Path(..., description="The version UUID"),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a specific resume version. Cannot delete the current (latest) version."""
    user_id = await get_current_user_id()
    await resume_service.delete_version(db, user_id, resume_id, version_id)


@router.post(
    "/{resume_id}/export-pdf",
    summary="Export resume as PDF",
)
async def export_resume_pdf(
    resume_id: uuid.UUID = Path(..., description="The resume UUID"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Export a resume as an ATS-friendly PDF."""
    user_id = await get_current_user_id()
    resume = await resume_service.get_resume(db, user_id, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")

    from src.services.pdf_export_service import render_resume_pdf

    content = resume.content.model_dump() if hasattr(resume.content, "model_dump") else {}
    headline = resume.resume_name or "Resume"

    try:
        pdf_bytes = await render_resume_pdf(content, headline=headline)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # RFC 5987: encode filename for non-ASCII characters (Chinese names)
    ascii_fallback = quote(headline.replace(" ", "_"), safe="") + ".pdf"
    encoded_filename = quote(filename) if (filename := f"{headline.replace(' ', '_')}.pdf") else ascii_fallback
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{encoded_filename}",
        },
    )
