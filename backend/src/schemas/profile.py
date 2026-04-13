from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CandidateProfileUpsert(BaseModel):
    """Request body for creating or updating a candidate profile."""

    headline: str = Field(default="", max_length=256, description="Professional headline")
    exit_story: str = Field(default="", description="Why you're looking for a new role")
    superpowers: list[str] = Field(default_factory=list, description="Core strengths")
    proof_points: list[dict[str, Any]] = Field(
        default_factory=list, description="Structured evidence with name/metric pairs",
    )
    compensation: dict[str, Any] = Field(default_factory=dict, description="Compensation expectations")
    location: dict[str, Any] = Field(default_factory=dict, description="Location preferences")
    preferences: dict[str, Any] = Field(default_factory=dict, description="Work style preferences")
    constraints: dict[str, Any] = Field(default_factory=dict, description="Hard constraints (visa, remote, etc.)")


class CandidateProfileResponse(BaseModel):
    """Full candidate profile returned by the API."""

    id: UUID
    headline: str
    exit_story: str
    superpowers: list[str]
    proof_points: list[dict[str, Any]]
    compensation: dict[str, Any]
    location: dict[str, Any]
    preferences: dict[str, Any]
    constraints: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProfileCompletenessResponse(BaseModel):
    """Profile completeness metrics."""

    total_fields: int
    filled_fields: int
    completeness_pct: float
    missing_high_value: list[str]
