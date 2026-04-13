"""CandidateProfile model — canonical structured source of truth for tailoring."""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, CommonBase, IDMixin, TimestampMixin


class CandidateProfile(IDMixin, TimestampMixin, Base):
    __tablename__ = "candidate_profiles"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True,
    )
    headline: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    exit_story: Mapped[str] = mapped_column(Text, nullable=False, default="")
    superpowers_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    proof_points_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    compensation_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    location_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    preferences_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    constraints_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
