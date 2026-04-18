from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """Request body for creating a project."""
    work_experience_id: UUID | None = None
    education_id: UUID | None = None
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="")
    tech_stack: list[str] = Field(default_factory=list)
    url: str = Field(default="", max_length=500)
    start_date: date | None = None
    end_date: date | None = None
    sort_order: int = Field(default=0)


class ProjectUpdate(BaseModel):
    """Request body for updating a project. All fields optional."""
    work_experience_id: UUID | None = None
    education_id: UUID | None = None
    name: str | None = None
    description: str | None = None
    tech_stack: list[str] | None = None
    url: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    sort_order: int | None = None


class ProjectResponse(BaseModel):
    """Full project returned by the API."""
    id: UUID
    profile_id: UUID
    work_experience_id: UUID | None
    education_id: UUID | None
    name: str
    description: str
    tech_stack: list[str]
    url: str
    start_date: date | None
    end_date: date | None
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
