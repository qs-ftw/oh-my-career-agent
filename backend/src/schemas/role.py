from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class RoleCreate(BaseModel):
    """Request body for creating a new target role."""

    role_name: str = Field(..., min_length=1, max_length=200, description="Target role name")
    role_type: str = Field(..., max_length=100, description="Role category, e.g. Backend Engineer")
    description: str = Field(default="", max_length=2000, description="Role description")
    keywords: list[str] = Field(default_factory=list, description="Search keywords")
    required_skills: list[str] = Field(default_factory=list, description="Required skills")
    bonus_skills: list[str] = Field(default_factory=list, description="Nice-to-have skills")
    priority: int = Field(default=0, ge=0, le=10, description="Priority rank (0=lowest)")
    source_jd: Optional[str] = Field(default=None, description="Original JD text if role derived from JD")


class RoleUpdate(BaseModel):
    """Request body for updating an existing target role. All fields optional."""

    role_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    role_type: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=2000)
    keywords: Optional[list[str]] = Field(default=None)
    required_skills: Optional[list[str]] = Field(default=None)
    bonus_skills: Optional[list[str]] = Field(default=None)
    priority: Optional[int] = Field(default=None, ge=0, le=10)
    source_jd: Optional[str] = Field(default=None)


class RoleResponse(BaseModel):
    """Full role detail returned by the API."""

    id: UUID
    role_name: str
    role_type: str
    description: str
    keywords: list[str]
    required_skills: list[str]
    bonus_skills: list[str]
    priority: int
    status: str = "active"
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RoleListResponse(BaseModel):
    """Paginated list of roles with minimal data."""

    items: list[RoleResponse]
    total: int = 0
