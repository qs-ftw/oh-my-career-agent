from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ResumeContent(BaseModel):
    """Structured resume content. Each section is stored as generic dicts/lists
    so the schema can evolve without requiring migrations for every change."""

    summary: str = ""
    skills: list[dict[str, Any]] = Field(default_factory=list)
    experiences: list[dict[str, Any]] = Field(default_factory=list)
    projects: list[dict[str, Any]] = Field(default_factory=list)
    highlights: list[dict[str, Any]] = Field(default_factory=list)
    metrics: list[dict[str, Any]] = Field(default_factory=list)
    interview_points: list[dict[str, Any]] = Field(default_factory=list)


class ResumeResponse(BaseModel):
    """Full resume detail returned by the API."""

    id: UUID
    target_role_id: UUID
    resume_name: str
    resume_type: str = "agent_generated"
    current_version_no: int = 1
    status: str = "draft"
    completeness_score: float = 0.0
    match_score: Optional[float] = None
    content: ResumeContent = Field(default_factory=ResumeContent)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResumeUpdate(BaseModel):
    """Request body for updating a resume."""

    resume_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    content: Optional[ResumeContent] = None
