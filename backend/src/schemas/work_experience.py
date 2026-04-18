from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class WorkExperienceCreate(BaseModel):
    """Request body for creating a work experience."""
    company_name: str = Field(..., min_length=1, max_length=200)
    company_url: str = Field(default="", max_length=500)
    location: str = Field(default="", max_length=100)
    role_title: str = Field(..., min_length=1, max_length=200)
    start_date: date
    end_date: date | None = None
    description: str = Field(default="")
    sort_order: int = Field(default=0)


class WorkExperienceUpdate(BaseModel):
    """Request body for updating a work experience. All fields optional."""
    company_name: str | None = None
    company_url: str | None = None
    location: str | None = None
    role_title: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None
    sort_order: int | None = None


class WorkExperienceResponse(BaseModel):
    """Full work experience returned by the API."""
    id: UUID
    profile_id: UUID
    company_name: str
    company_url: str
    location: str
    role_title: str
    start_date: date
    end_date: date | None
    description: str
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
