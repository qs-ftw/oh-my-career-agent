from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SuggestionResponse(BaseModel):
    """Full suggestion detail returned by the API."""

    id: UUID
    suggestion_type: str
    target_role_id: Optional[UUID] = None
    resume_id: Optional[UUID] = None
    title: str
    content: str = ""
    impact_score: float = 0.0
    risk_level: str = "low"
    status: str = "pending"
    created_at: datetime

    model_config = {"from_attributes": True}


class SuggestionActionRequest(BaseModel):
    """Request body for accepting or rejecting a suggestion."""

    notes: Optional[str] = Field(default=None, max_length=2000, description="Optional user notes")
