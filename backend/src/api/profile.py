"""Candidate profile endpoints — single canonical profile per user."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user_id, get_current_workspace_id
from src.schemas.profile import (
    CareerProfileResponse,
    CareerProfileUpsert,
    ProfileCompletenessResponse,
)
from src.services import profile_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get(
    "",
    response_model=CareerProfileResponse | None,
    summary="Get candidate profile",
)
async def get_profile(
    db: AsyncSession = Depends(get_db),
) -> CareerProfileResponse | None:
    """Return the current user's candidate profile, or null if not set."""
    user_id = await get_current_user_id()
    workspace_id = await get_current_workspace_id()
    return await profile_service.get_profile(db, user_id, workspace_id)


@router.put(
    "",
    response_model=CareerProfileResponse,
    summary="Create or update candidate profile",
)
async def upsert_profile(
    body: CareerProfileUpsert,
    db: AsyncSession = Depends(get_db),
) -> CareerProfileResponse:
    """Upsert the current user's candidate profile."""
    user_id = await get_current_user_id()
    workspace_id = await get_current_workspace_id()
    return await profile_service.upsert_profile(db, user_id, workspace_id, body)


@router.get(
    "/completeness",
    response_model=ProfileCompletenessResponse,
    summary="Get profile completeness metrics",
)
async def get_completeness(
    db: AsyncSession = Depends(get_db),
) -> ProfileCompletenessResponse:
    """Return profile completeness metrics."""
    user_id = await get_current_user_id()
    workspace_id = await get_current_workspace_id()
    return await profile_service.get_completeness(db, user_id, workspace_id)


@router.post(
    "/import-resume",
    summary="Import profile data from a PDF resume",
)
async def import_resume(
    file: UploadFile = File(..., description="PDF resume file"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Upload a PDF resume, extract text, parse via LLM, and auto-fill profile data.

    Returns the extracted profile, created work experiences, and projects.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="只支持PDF格式的简历文件")

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="文件大小不能超过10MB")

    user_id = await get_current_user_id()
    workspace_id = await get_current_workspace_id()

    try:
        from src.services.resume_import_service import import_resume_pdf

        result = await import_resume_pdf(db, user_id, workspace_id, file_bytes)
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Resume import failed: {e}")
        raise HTTPException(status_code=500, detail=f"简历解析失败: {e}")
