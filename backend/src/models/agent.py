"""AgentRun and UpdateSuggestion audit models."""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, CommonBase, IDMixin, TimestampMixin


class AgentRun(CommonBase):
    __tablename__ = "agent_runs"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True,
    )
    run_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_type: Mapped[str | None] = mapped_column(String(64), nullable=True, default=None)
    source_ref_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, default=None
    )
    input_payload_json: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=None
    )
    output_payload_json: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=None
    )
    explainability_notes: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    review_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending",
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="running",
    )


class UpdateSuggestion(IDMixin, TimestampMixin, Base):
    __tablename__ = "update_suggestions"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True,
    )
    suggestion_type: Mapped[str] = mapped_column(
        String(32), nullable=False,
    )
    target_role_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("target_roles.id"), nullable=True, default=None,
    )
    resume_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=True, default=None,
    )
    source_type: Mapped[str | None] = mapped_column(String(64), nullable=True, default=None)
    source_ref_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, default=None
    )
    source_achievement_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("achievements.id"), nullable=True, default=None,
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    impact_score_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    risk_level: Mapped[str] = mapped_column(
        String(16), nullable=False, default="low",
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending",
    )
    applied_resume_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_versions.id"), nullable=True, default=None,
    )
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    apply_result_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
