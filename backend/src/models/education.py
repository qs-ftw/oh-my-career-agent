"""Education model — an academic institution or degree program."""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, IDMixin, TimestampMixin


class Education(IDMixin, TimestampMixin, Base):
    __tablename__ = "educations"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("career_profiles.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    institution_name: Mapped[str] = mapped_column(String(200), nullable=False)
    institution_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    degree: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    field_of_study: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    location: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    gpa: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
