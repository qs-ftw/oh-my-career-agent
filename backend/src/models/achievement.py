"""Achievement, AchievementRoleMatch, and AchievementResumeLink models."""

import uuid
from datetime import datetime

from sqlalchemy import String, Float, ForeignKey, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, IDMixin, TimestampMixin


class Achievement(IDMixin, TimestampMixin, Base):
    __tablename__ = "achievements"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True,
    )
    source_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="manual",
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    raw_content: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    parsed_summary: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    technical_points_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    challenges_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    solutions_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    metrics_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    interview_points_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    tags_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    importance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class AchievementRoleMatch(IDMixin, TimestampMixin, Base):
    __tablename__ = "achievement_role_matches"

    achievement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("achievements.id"), nullable=False, index=True,
    )
    target_role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("target_roles.id"), nullable=False, index=True,
    )
    match_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    match_reason: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)


class AchievementResumeLink(IDMixin, TimestampMixin, Base):
    __tablename__ = "achievement_resume_links"

    achievement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("achievements.id"), nullable=False, index=True,
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False, index=True,
    )
    resume_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_versions.id"), nullable=True, default=None,
    )
    applied_section: Mapped[str | None] = mapped_column(String(128), nullable=True, default=None)
    applied_mode: Mapped[str | None] = mapped_column(String(32), nullable=True, default=None)
