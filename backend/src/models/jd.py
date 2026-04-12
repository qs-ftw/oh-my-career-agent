"""JDSnapshot and JDResumeTask models."""

import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Float, ForeignKey, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, CommonBase, IDMixin, TimestampMixin


class JDSnapshot(IDMixin, TimestampMixin, Base):
    __tablename__ = "jd_snapshots"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True,
    )
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, default="manual")
    raw_jd: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    parsed_role_name: Mapped[str | None] = mapped_column(String(256), nullable=True, default=None)
    parsed_keywords_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    parsed_required_skills_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    parsed_bonus_items_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    parsed_style_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)


class JDResumeTask(CommonBase):
    __tablename__ = "jd_resume_tasks"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True,
    )
    jd_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jd_snapshots.id"), nullable=False, index=True,
    )
    mode: Mapped[str] = mapped_column(
        String(32), nullable=False, default="generate_new",
    )
    base_resume_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=True, default=None,
    )
    generated_resume_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=True, default=None,
    )
    ability_match_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    resume_match_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    readiness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recommendation: Mapped[str] = mapped_column(
        String(32), nullable=False, default="not_recommended",
    )
    missing_items_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    optimization_notes_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending",
    )
