"""JD (Job Description) endpoints — database-backed parse, tailor, and task retrieval."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user_id, get_current_workspace_id
from src.schemas.jd import JDInput, JDParsedResponse, JDTailorResponse
from src.services import jd_service

router = APIRouter(prefix="/jd", tags=["jd"])


@router.post(
    "/parse",
    response_model=JDParsedResponse,
    status_code=status.HTTP_200_OK,
    summary="Parse a raw JD into structured data",
)
async def parse_jd(
    body: JDInput,
    db: AsyncSession = Depends(get_db),
) -> JDParsedResponse:
    """Extract role name, skills, keywords, and style from raw JD text."""
    user_id = await get_current_user_id()
    workspace_id = await get_current_workspace_id()
    return await jd_service.parse_jd(db, user_id, workspace_id, body.raw_jd)


@router.post(
    "/tailor",
    response_model=JDTailorResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a tailored resume for a JD",
)
async def tailor_jd(
    body: JDInput,
    db: AsyncSession = Depends(get_db),
) -> JDTailorResponse:
    """Generate or tune a resume specifically for the given JD.

    This runs the full JD tailoring pipeline: parsing + tailoring + scoring.
    May take 10-30 seconds.
    """
    user_id = await get_current_user_id()
    workspace_id = await get_current_workspace_id()
    return await jd_service.tailor_jd(
        db, user_id, workspace_id,
        raw_jd=body.raw_jd,
        mode=body.mode,
        base_resume_id=body.base_resume_id,
    )


@router.get(
    "/tasks/{task_id}",
    response_model=dict[str, Any],
    summary="Get JD task result",
)
async def get_task(
    task_id: uuid.UUID = Path(..., description="The JD task UUID"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Retrieve the status/result of a JD processing task."""
    user_id = await get_current_user_id()
    result = await jd_service.get_task(db, user_id, task_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return result


@router.post(
    "/tasks/{task_id}/export-pdf",
    summary="Export JD-tailored resume as PDF",
)
async def export_jd_task_pdf(
    task_id: uuid.UUID = Path(..., description="The JD task UUID"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Export the JD-tailored resume from a completed task as a PDF."""
    user_id = await get_current_user_id()

    # Get the task to find the generated resume
    task = await jd_service.get_task(db, user_id, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    from src.models.jd import JDResumeTask
    from sqlalchemy import select

    stmt = select(JDResumeTask).where(JDResumeTask.id == task_id, JDResumeTask.user_id == user_id)
    result = await session.execute(stmt) if False else await db.execute(stmt)
    jd_task = result.scalar_one_or_none()
    if jd_task is None or not jd_task.generated_resume_id:
        raise HTTPException(status_code=404, detail="No generated resume found for this task")

    # Get the resume content
    resume = await resume_service.get_resume(db, user_id, jd_task.generated_resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Generated resume not found")

    from src.services.pdf_export_service import render_resume_pdf

    content = resume.content.model_dump() if hasattr(resume.content, "model_dump") else {}
    headline = f"JD_{task_id}_resume"

    try:
        pdf_bytes = await render_resume_pdf(content, headline=headline)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="jd_tailored_resume.pdf"'},
    )
