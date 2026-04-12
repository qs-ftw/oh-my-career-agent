"""Stub service for target role operations.

All methods return mock data. Replace with real DB queries when models are wired up.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from src.schemas.role import RoleCreate, RoleResponse, RoleUpdate


def _mock_role(**overrides: object) -> RoleResponse:
    """Return a consistently shaped mock role."""
    now = datetime.now(timezone.utc)
    defaults: dict = {
        "id": uuid.uuid4(),
        "role_name": "Senior Backend Engineer",
        "role_type": "Backend",
        "description": "Design and build scalable backend services.",
        "keywords": ["distributed systems", "go", "kubernetes"],
        "required_skills": ["Go", "PostgreSQL", "gRPC"],
        "bonus_skills": ["Kubernetes", "Terraform"],
        "priority": 5,
        "status": "active",
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return RoleResponse(**defaults)


async def create_role(data: RoleCreate) -> RoleResponse:
    """Create a new target role (stub)."""
    return _mock_role(
        role_name=data.role_name,
        role_type=data.role_type,
        description=data.description,
        keywords=data.keywords,
        required_skills=data.required_skills,
        bonus_skills=data.bonus_skills,
        priority=data.priority,
    )


async def list_roles() -> list[RoleResponse]:
    """List all target roles for the current user (stub)."""
    return []


async def get_role(role_id: uuid.UUID) -> RoleResponse | None:
    """Return a single role by ID (stub)."""
    return _mock_role(id=role_id)


async def update_role(role_id: uuid.UUID, data: RoleUpdate) -> RoleResponse | None:
    """Update a target role (stub)."""
    return _mock_role(id=role_id)


async def delete_role(role_id: uuid.UUID) -> None:
    """Soft-delete a target role (stub)."""
    return None
