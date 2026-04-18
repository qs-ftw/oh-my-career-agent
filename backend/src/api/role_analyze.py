"""Role analysis endpoints — preview only, no side effects."""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter

from src.services import role_analyze_service

router = APIRouter(prefix="/roles", tags=["roles"])


class AnalyzeJDRequest(BaseModel):
    raw_jd: str = Field(..., min_length=10, description="Raw job description text")


class AnalyzeNameRequest(BaseModel):
    role_name: str = Field(..., min_length=1, max_length=200, description="Target role name")


class RoleAnalysisResponse(BaseModel):
    role_name: str
    role_type: str
    description: str
    required_skills: list[str]
    bonus_skills: list[str]
    keywords: list[str]


@router.post(
    "/analyze-jd",
    response_model=RoleAnalysisResponse,
    summary="Analyze JD text (preview only)",
)
async def analyze_jd(body: AnalyzeJDRequest) -> RoleAnalysisResponse:
    """Parse a JD and return structured role data without creating anything."""
    result = await role_analyze_service.analyze_jd(body.raw_jd)
    return RoleAnalysisResponse(**result)


@router.post(
    "/analyze-name",
    response_model=RoleAnalysisResponse,
    summary="Analyze role name (preview only)",
)
async def analyze_name(body: AnalyzeNameRequest) -> RoleAnalysisResponse:
    """Generate typical JD data from a role name without creating anything."""
    result = await role_analyze_service.analyze_name(body.role_name)
    return RoleAnalysisResponse(**result)
