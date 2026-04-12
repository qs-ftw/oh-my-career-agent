from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.schemas.resume import ResumeContent


class JDInput(BaseModel):
    """Request body for JD-related operations."""

    raw_jd: str = Field(..., min_length=10, description="Raw job description text")
    mode: str = Field(
        default="generate_new",
        pattern="^(generate_new|tune_existing)$",
        description="generate_new creates from scratch; tune_existing adapts a base resume",
    )
    base_resume_id: Optional[UUID] = Field(
        default=None, description="Required when mode=tune_existing"
    )


class JDParsedResponse(BaseModel):
    """Structured data extracted from a JD."""

    role_name: str = ""
    keywords: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    bonus_items: list[str] = Field(default_factory=list)
    style: dict[str, Any] = Field(default_factory=dict)


class JDTailorResponse(BaseModel):
    """Full JD tailoring result including a generated/resumed resume and scores."""

    resume: ResumeContent = Field(default_factory=ResumeContent)
    ability_match_score: float = 0.0
    resume_match_score: float = 0.0
    readiness_score: float = 0.0
    recommendation: str = ""
    missing_items: list[str] = Field(default_factory=list)
    optimization_notes: list[str] = Field(default_factory=list)
