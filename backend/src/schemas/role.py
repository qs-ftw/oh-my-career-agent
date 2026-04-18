from __future__ import annotations

from datetime import datetime
from uuid import UUID

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
    source_jd: str | None = Field(
        default=None, description="Original JD text if role derived from JD"
    )
    skip_init: bool = Field(default=False, description="Skip resume/gap generation if True")


class RoleUpdate(BaseModel):
    """Request body for updating an existing target role. All fields optional."""

    role_name: str | None = Field(default=None, min_length=1, max_length=200)
    role_type: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    keywords: list[str] | None = Field(default=None)
    required_skills: list[str] | None = Field(default=None)
    bonus_skills: list[str] | None = Field(default=None)
    priority: int | None = Field(default=None, ge=0, le=10)
    source_jd: str | None = Field(default=None)
    status: str | None = Field(default=None, pattern="^(active|paused)$")


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
