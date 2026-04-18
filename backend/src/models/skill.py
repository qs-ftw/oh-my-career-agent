"""SkillEntity model."""

import uuid

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, IDMixin, TimestampMixin


class SkillEntity(IDMixin, TimestampMixin, Base):
    __tablename__ = "skill_entities"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True,
    )
    skill_name: Mapped[str] = mapped_column(String(256), nullable=False)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True, default=None)
    proficiency_level: Mapped[str | None] = mapped_column(String(32), nullable=True, default=None)
    evidence_strength: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    evidence_refs_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
