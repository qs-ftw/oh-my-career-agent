"""Achievement, AchievementRoleMatch, and AchievementResumeLink models."""

import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, IDMixin, TimestampMixin


class Achievement(IDMixin, TimestampMixin, Base):
    __tablename__ = "achievements"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("career_profiles.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True, default=None, index=True,
    )
    work_experience_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("work_experiences.id", ondelete="SET NULL"),
        nullable=True, default=None, index=True,
    )
    education_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("educations.id", ondelete="SET NULL"),
        nullable=True, default=None, index=True,
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    raw_content: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    parsed_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    importance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="raw")
    date_occurred: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)

    # Interactive analysis fields
    analysis_chat: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=None)
    enrichment_suggestions: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=None)
    polished_content: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    display_format: Mapped[str] = mapped_column(String(20), nullable=False, default="raw")


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
