"""User model."""


from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, IDMixin, TimestampMixin


class User(IDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True, default=None)
