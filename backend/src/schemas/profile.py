from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CareerProfileUpsert(BaseModel):
    """Request body for creating or updating a career profile."""
    name: str = Field(default="", max_length=100)
    headline: str = Field(default="", max_length=200)
    email: str = Field(default="", max_length=200)
    phone: str = Field(default="", max_length=50)
    linkedin_url: str = Field(default="", max_length=500)
    portfolio_url: str = Field(default="", max_length=500)
    github_url: str = Field(default="", max_length=500)
    location: str = Field(default="", max_length=100)
    professional_summary: str = Field(default="")
    skill_categories: dict[str, list[str]] = Field(default_factory=dict)


class CareerProfileResponse(BaseModel):
    """Full career profile returned by the API."""
    id: UUID
    name: str
    headline: str
    email: str
    phone: str
    linkedin_url: str
    portfolio_url: str
    github_url: str
    location: str
    professional_summary: str
    skill_categories: dict[str, list[str]]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProfileCompletenessResponse(BaseModel):
    """Profile completeness metrics."""
    total_fields: int
    filled_fields: int
    completeness_pct: float
    missing_high_value: list[str]
    missing_low_value: list[str]
