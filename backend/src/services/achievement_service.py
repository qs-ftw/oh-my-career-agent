"""Stub service for achievement operations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from src.schemas.achievement import AchievementCreate, AchievementResponse


def _mock_achievement(**overrides: object) -> AchievementResponse:
    now = datetime.now(timezone.utc)
    defaults: dict = {
        "id": uuid.uuid4(),
        "title": "Designed event-driven order processing pipeline",
        "raw_content": "Led the redesign of the order processing system using Kafka and Go.",
        "parsed_summary": "Redesigned order processing to be event-driven using Kafka.",
        "technical_points": [{"point": "Implemented Kafka consumer group for order events"}],
        "challenges": [],
        "solutions": [],
        "metrics": [{"metric": "Reduced processing latency by 40%"}],
        "interview_points": [],
        "tags": ["backend", "kafka", "go"],
        "importance_score": 0.85,
        "created_at": now,
    }
    defaults.update(overrides)
    return AchievementResponse(**defaults)


async def create_achievement(data: AchievementCreate) -> AchievementResponse:
    return _mock_achievement(title=data.title, raw_content=data.raw_content)


async def list_achievements() -> list[AchievementResponse]:
    return []


async def get_achievement(achievement_id: uuid.UUID) -> AchievementResponse | None:
    return _mock_achievement(id=achievement_id)


async def analyze_achievement(achievement_id: uuid.UUID) -> AchievementResponse | None:
    """Trigger AI analysis on an achievement (stub)."""
    return _mock_achievement(id=achievement_id)
