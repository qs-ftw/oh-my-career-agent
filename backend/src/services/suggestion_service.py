"""Stub service for suggestion operations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from src.schemas.suggestion import SuggestionResponse


def _mock_suggestion(**overrides: object) -> SuggestionResponse:
    now = datetime.now(timezone.utc)
    defaults: dict = {
        "id": uuid.uuid4(),
        "suggestion_type": "resume_update",
        "target_role_id": uuid.uuid4(),
        "resume_id": uuid.uuid4(),
        "title": "Add Kafka experience to Skills section",
        "content": "Include event-driven architecture experience with Kafka consumer groups.",
        "impact_score": 0.8,
        "risk_level": "low",
        "status": "pending",
        "created_at": now,
    }
    defaults.update(overrides)
    return SuggestionResponse(**defaults)


async def list_suggestions(
    suggestion_type: str | None = None,
    status: str | None = None,
    target_role_id: uuid.UUID | None = None,
) -> list[SuggestionResponse]:
    return []


async def accept_suggestion(
    suggestion_id: uuid.UUID, notes: str | None = None
) -> SuggestionResponse | None:
    return _mock_suggestion(id=suggestion_id, status="accepted")


async def reject_suggestion(
    suggestion_id: uuid.UUID, notes: str | None = None
) -> SuggestionResponse | None:
    return _mock_suggestion(id=suggestion_id, status="rejected")
