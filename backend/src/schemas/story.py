from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class StoryCreate(BaseModel):
    """Request body for creating an interview story."""

    title: str = Field(..., min_length=1, max_length=256)
    theme: str = Field(default="general", max_length=128)
    source_type: str = Field(..., max_length=64, description="achievement | jd_task")
    source_ref_id: UUID | None = None
    story_json: dict[str, Any] = Field(default_factory=dict)
    best_for_json: list[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)


class StoryUpdate(BaseModel):
    """Request body for updating an interview story. All fields optional."""

    title: str | None = Field(default=None, min_length=1, max_length=256)
    theme: str | None = Field(default=None, max_length=128)
    story_json: dict[str, Any] | None = None
    best_for_json: list[str] | None = None
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)


class StoryResponse(BaseModel):
    """Full interview story detail."""

    id: UUID
    title: str
    theme: str
    source_type: str
    source_ref_id: UUID | None = None
    story_json: dict[str, Any]
    best_for_json: list[str]
    confidence_score: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StoryListResponse(BaseModel):
    items: list[StoryResponse]
    total: int = 0
