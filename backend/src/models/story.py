"""InterviewStory model — reusable STAR-structured interview stories."""

import uuid

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import CommonBase


class InterviewStory(CommonBase):
    __tablename__ = "interview_stories"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True,
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    theme: Mapped[str] = mapped_column(String(128), nullable=False, default="general")
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_ref_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, default=None,
    )
    story_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    best_for_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
