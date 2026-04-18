from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EducationCreate(BaseModel):
    """Request body for creating an education record."""
    institution_name: str = Field(..., min_length=1, max_length=200)
    institution_url: str = Field(default="", max_length=500)
    degree: str = Field(default="", max_length=50)
    field_of_study: str = Field(default="", max_length=200)
    location: str = Field(default="", max_length=100)
    start_date: date
    end_date: date | None = None
    gpa: str = Field(default="", max_length=20)
    description: str = Field(default="")
    sort_order: int = Field(default=0)


class EducationUpdate(BaseModel):
    """Request body for updating an education record. All fields optional."""
    institution_name: str | None = None
    institution_url: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    location: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    gpa: str | None = None
    description: str | None = None
    sort_order: int | None = None


class EducationResponse(BaseModel):
    """Full education returned by the API."""
    id: UUID
    profile_id: UUID
    institution_name: str
    institution_url: str
    degree: str
    field_of_study: str
    location: str
    start_date: date
    end_date: date | None
    gpa: str
    description: str
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
