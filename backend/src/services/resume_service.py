"""Stub service for resume operations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from src.schemas.resume import ResumeContent, ResumeResponse, ResumeUpdate


def _mock_resume(**overrides: object) -> ResumeResponse:
    now = datetime.now(timezone.utc)
    defaults: dict = {
        "id": uuid.uuid4(),
        "target_role_id": uuid.uuid4(),
        "resume_name": "Senior Backend Engineer Resume",
        "resume_type": "agent_generated",
        "current_version_no": 1,
        "status": "draft",
        "completeness_score": 0.65,
        "match_score": None,
        "content": ResumeContent(
            summary="Experienced backend engineer with 5+ years of experience.",
            skills=[{"category": "Languages", "items": ["Go", "Python", "SQL"]}],
            experiences=[],
            projects=[],
            highlights=[],
            metrics=[],
            interview_points=[],
        ),
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return ResumeResponse(**defaults)


async def list_resumes() -> list[ResumeResponse]:
    return []


async def get_resume(resume_id: uuid.UUID) -> ResumeResponse | None:
    return _mock_resume(id=resume_id)


async def update_resume(resume_id: uuid.UUID, data: ResumeUpdate) -> ResumeResponse | None:
    return _mock_resume(id=resume_id)


async def list_versions(resume_id: uuid.UUID) -> list[dict[str, Any]]:
    return []


async def apply_suggestion(resume_id: uuid.UUID, suggestion_id: uuid.UUID) -> ResumeResponse | None:
    return _mock_resume(id=resume_id)
