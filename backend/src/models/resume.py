"""Resume and ResumeVersion models."""

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, CommonBase, IDMixin, TimestampMixin


class Resume(CommonBase):
    __tablename__ = "resumes"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True,
    )
    target_role_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("target_roles.id"), nullable=True, default=None, index=True,
    )
    resume_name: Mapped[str] = mapped_column(String(256), nullable=False)
    resume_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="master",
    )
    parent_resume_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=True, default=None,
    )
    current_version_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="draft",
    )
    completeness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    match_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class ResumeVersion(IDMixin, TimestampMixin, Base):
    __tablename__ = "resume_versions"

    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False, index=True,
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    content_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    generated_by: Mapped[str] = mapped_column(
        String(32), nullable=False, default="user",
    )
    source_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="manual_edit",
    )
    source_ref_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, default=None,
    )
    summary_note: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    completeness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    match_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
