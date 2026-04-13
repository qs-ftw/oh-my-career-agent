from __future__ import annotations

from datetime import datetime
from uuid import UUID

from typing import Any

from pydantic import BaseModel, Field


class SuggestionResponse(BaseModel):
    """Full suggestion detail returned by the API."""

    id: UUID
    suggestion_type: str
    target_role_id: UUID | None = None
    resume_id: UUID | None = None
    title: str
    content: str = ""
    impact_score: float = 0.0
    risk_level: str = "low"
    status: str = "pending"
    applied_resume_version_id: UUID | None = None
    apply_result: dict[str, Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SuggestionActionRequest(BaseModel):
    """Request body for accepting or rejecting a suggestion."""

    notes: str | None = Field(default=None, max_length=2000, description="Optional user notes")
