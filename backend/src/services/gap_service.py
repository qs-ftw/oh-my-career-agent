"""Stub service for gap operations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from src.schemas.gap import GapResponse, GapUpdate


def _mock_gap(**overrides: object) -> GapResponse:
    now = datetime.now(timezone.utc)
    defaults: dict = {
        "id": uuid.uuid4(),
        "target_role_id": uuid.uuid4(),
        "skill_name": "Kubernetes",
        "gap_type": "skill",
        "priority": 3,
        "current_state": "Basic pod/deployment knowledge",
        "target_state": "Can design and operate production K8s clusters",
        "evidence": [],
        "improvement_plan": None,
        "progress": 0.2,
        "status": "in_progress",
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return GapResponse(**defaults)


async def list_gaps(role_id: uuid.UUID | None = None) -> list[GapResponse]:
    return []


async def list_gaps_for_role(role_id: uuid.UUID) -> list[GapResponse]:
    return []


async def update_gap(gap_id: uuid.UUID, data: GapUpdate) -> GapResponse | None:
    return _mock_gap(id=gap_id)
