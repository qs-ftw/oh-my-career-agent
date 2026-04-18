from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AchievementCreate(BaseModel):
    """Request body for creating a new achievement."""
    project_id: UUID | None = None
    work_experience_id: UUID | None = None
    education_id: UUID | None = None
    title: str = Field(..., min_length=1, max_length=512)
    raw_content: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)
    source_type: str = Field(default="manual", max_length=50)
    date_occurred: date | None = None


class AchievementResponse(BaseModel):
    """Full achievement detail returned by the API."""
    id: UUID
    profile_id: UUID
    project_id: UUID | None = None
    work_experience_id: UUID | None = None
    education_id: UUID | None = None
    title: str
    raw_content: str
    parsed_data: dict[str, Any] | None = None
    tags: list[str] = Field(default_factory=list)
    importance_score: float = 0.0
    source_type: str = "manual"
    status: str = "raw"
    date_occurred: date | None = None
    analysis_error: str | None = None
    analysis_chat: list[dict[str, Any]] | None = None
    enrichment_suggestions: list[dict[str, Any]] | None = None
    polished_content: dict[str, Any] | None = None
    display_format: str = "raw"
    created_at: datetime

    model_config = {"from_attributes": True}


_UNSET = object()


class AchievementUpdate(BaseModel):
    """Request body for updating an achievement. All fields optional.

    Nullable fields (project_id, work_experience_id) use a sentinel _UNSET
    to distinguish "not provided" from "explicitly set to None".
    """
    title: str | None = None
    raw_content: str | None = None
    project_id: UUID | None | object = _UNSET
    work_experience_id: UUID | None | object = _UNSET
    tags: list[str] | None = None
    display_format: str | None = None


class AchievementAnalysisRequest(BaseModel):
    """Request to trigger AI analysis on an achievement."""
    achievement_id: UUID
