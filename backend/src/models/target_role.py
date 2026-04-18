"""TargetRole and RoleCapabilityModel."""

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import CommonBase


class TargetRole(CommonBase):
    __tablename__ = "target_roles"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True,
    )
    role_name: Mapped[str] = mapped_column(String(256), nullable=False)
    role_type: Mapped[str] = mapped_column(String(64), nullable=False, default="full_time")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    keywords_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    required_skills_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    bonus_skills_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="active",
    )
    source_jd_summary: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)


class RoleCapabilityModel(CommonBase):
    __tablename__ = "role_capabilities"

    target_role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("target_roles.id"), nullable=False, index=True,
    )
    core_capabilities_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    secondary_capabilities_json: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=None
    )
    bonus_capabilities_json: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=None
    )
    project_requirements_json: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=None
    )
    evaluation_rules_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
