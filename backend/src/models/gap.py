"""GapItem model."""

import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, IDMixin, TimestampMixin


class GapItem(IDMixin, TimestampMixin, Base):
    __tablename__ = "gap_items"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True,
    )
    target_role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("target_roles.id"), nullable=False, index=True,
    )
    skill_name: Mapped[str] = mapped_column(String(256), nullable=False)
    gap_type: Mapped[str] = mapped_column(
        String(32), nullable=False,
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_state: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    target_state: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    evidence_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    improvement_plan_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    progress: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="open",
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True, default=None,
    )
