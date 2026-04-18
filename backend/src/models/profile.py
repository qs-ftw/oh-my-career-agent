"""CareerProfile model — canonical structured career data."""

import uuid

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, IDMixin, TimestampMixin


class CareerProfile(IDMixin, TimestampMixin, Base):
    __tablename__ = "career_profiles"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    headline: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    phone: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    linkedin_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    portfolio_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    github_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    location: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    professional_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    skill_categories: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
