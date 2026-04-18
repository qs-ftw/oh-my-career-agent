"""WorkExperience model — a role at a company."""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, IDMixin, TimestampMixin


class WorkExperience(IDMixin, TimestampMixin, Base):
    __tablename__ = "work_experiences"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("career_profiles.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    company_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    location: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    role_title: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
