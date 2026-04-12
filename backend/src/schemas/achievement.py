from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AchievementCreate(BaseModel):
    """Request body for creating a new achievement."""

    source_type: str = Field(
        ..., max_length=50, description="Origin type, e.g. git_commit, slack_message, manual"
    )
    title: str = Field(..., min_length=1, max_length=300, description="Short achievement title")
    raw_content: str = Field(..., min_length=1, description="Raw achievement text")
    tags: Optional[list[str]] = Field(default=None, description="Optional tags")


class AchievementResponse(BaseModel):
    """Full achievement detail returned by the API."""

    id: UUID
    title: str
    raw_content: str
    parsed_summary: Optional[str] = None
    technical_points: list[dict[str, Any]] = Field(default_factory=list)
    challenges: list[dict[str, Any]] = Field(default_factory=list)
    solutions: list[dict[str, Any]] = Field(default_factory=list)
    metrics: list[dict[str, Any]] = Field(default_factory=list)
    interview_points: list[dict[str, Any]] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    importance_score: float = 0.0
    created_at: datetime

    model_config = {"from_attributes": True}


class AchievementAnalysisRequest(BaseModel):
    """Request to trigger AI analysis on an achievement."""

    achievement_id: UUID
