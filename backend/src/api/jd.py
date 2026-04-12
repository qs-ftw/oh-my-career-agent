"""JD (Job Description) endpoints — stubs returning mock data."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Path, status

from src.schemas.jd import JDInput, JDParsedResponse, JDTailorResponse
from src.services import jd_service

router = APIRouter(prefix="/jd", tags=["jd"])


@router.post(
    "/parse",
    response_model=JDParsedResponse,
    status_code=status.HTTP_200_OK,
    summary="Parse a raw JD into structured data",
)
async def parse_jd(body: JDInput) -> JDParsedResponse:
    """Extract role name, skills, keywords, and style from raw JD text."""
    return await jd_service.parse_jd(body.raw_jd)


@router.post(
    "/tailor",
    response_model=JDTailorResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a tailored resume for a JD",
)
async def tailor_jd(body: JDInput) -> JDTailorResponse:
    """Generate or tune a resume specifically for the given JD."""
    return await jd_service.tailor_jd(
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
) -> dict[str, Any]:
    """Retrieve the status/result of an asynchronous JD processing task."""
    return await jd_service.get_task(task_id)
