from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class GapResponse(BaseModel):
    """Full gap detail returned by the API."""

    id: UUID
    target_role_id: UUID
    skill_name: str
    gap_type: str = "skill"
    priority: int = 0
    current_state: str = ""
    target_state: str = ""
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    improvement_plan: Optional[dict[str, Any]] = None
    progress: float = 0.0
    status: str = "not_started"
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GapUpdate(BaseModel):
    """Request body for updating a gap."""

    status: Optional[str] = Field(default=None, pattern="^(not_started|in_progress|completed)$")
    progress: Optional[float] = Field(default=None, ge=0.0, le=1.0)
