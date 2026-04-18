from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    """Contact information for resume export. Empty fields are omitted from PDF."""

    email: str = ""
    phone: str = ""
    linkedin_url: str = ""
    portfolio_url: str = ""
    location: str = ""


class ResumeContent(BaseModel):
    """Structured resume content. Each section is stored as generic dicts/lists
    so the schema can evolve without requiring migrations for every change."""

    summary: str = ""
    skills: list[Any] = Field(default_factory=list)
    experiences: list[dict[str, Any]] = Field(default_factory=list)
    projects: list[dict[str, Any]] = Field(default_factory=list)
    highlights: list[Any] = Field(default_factory=list)
    metrics: list[dict[str, Any]] = Field(default_factory=list)
    interview_points: list[Any] = Field(default_factory=list)
    contact: ContactInfo = Field(default_factory=ContactInfo)


class ResumeResponse(BaseModel):
    """Full resume detail returned by the API."""

    id: UUID
    target_role_id: UUID
    resume_name: str
    resume_type: str = "agent_generated"
    current_version_no: int = 1
    status: str = "draft"
    completeness_score: float = 0.0
    match_score: float | None = None
    content: ResumeContent = Field(default_factory=ResumeContent)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResumeUpdate(BaseModel):
    """Request body for updating a resume."""

    resume_name: str | None = Field(default=None, min_length=1, max_length=200)
    content: ResumeContent | None = None
