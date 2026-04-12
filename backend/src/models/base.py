"""Base ORM mixins and common declarative base.

``CommonBase`` combines ``IDMixin``, ``TimestampMixin``, and
``SoftDeleteMixin`` so that every concrete model inherits a consistent set
of columns without repeating boilerplate.
"""

import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 declarative base used across all models."""

    pass


class IDMixin:
    """Provides a UUID primary-key column."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )


class TimestampMixin:
    """Provides ``created_at`` and ``updated_at`` columns auto-managed by the DB."""

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Provides a nullable ``deleted_at`` column for soft-delete support."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        default=None,
    )


class CommonBase(IDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Abstract parent for all concrete models.

    Combines id, timestamps, and soft-delete into one convenient class.
    Subclasses must set ``__tablename__`` and ``__table_args__`` as needed.
    """

    __abstract__ = True
