"""Database-backed service for suggestion operations."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.agent import UpdateSuggestion
from src.schemas.suggestion import SuggestionResponse

logger = logging.getLogger(__name__)


def _to_response(s: UpdateSuggestion) -> SuggestionResponse:
    """Convert an UpdateSuggestion ORM instance to SuggestionResponse.

    Handles type mismatches:
    - content_json (dict) -> content (str)
    - impact_score_json (dict) -> impact_score (float)
    """
    content_str = ""
    if s.content_json:
        if isinstance(s.content_json, str):
            content_str = s.content_json
        elif isinstance(s.content_json, dict):
            content_str = s.content_json.get("text", json.dumps(s.content_json, ensure_ascii=False))
        else:
            content_str = json.dumps(s.content_json, ensure_ascii=False)

    impact_score = 0.0
    if s.impact_score_json:
        if isinstance(s.impact_score_json, (int, float)):
            impact_score = float(s.impact_score_json)
        elif isinstance(s.impact_score_json, dict):
            impact_score = float(s.impact_score_json.get("score", 0.0))

    return SuggestionResponse(
        id=s.id,
        suggestion_type=s.suggestion_type,
        target_role_id=s.target_role_id,
        resume_id=s.resume_id,
        title=s.title,
        content=content_str,
        impact_score=impact_score,
        risk_level=s.risk_level,
        status=s.status,
        created_at=s.created_at,
    )


async def list_suggestions(
    session: AsyncSession,
    user_id: uuid.UUID,
    suggestion_type: str | None = None,
    status: str | None = None,
    target_role_id: uuid.UUID | None = None,
) -> list[SuggestionResponse]:
    """Return suggestions for a user with optional filters."""
    stmt = (
        select(UpdateSuggestion)
        .where(UpdateSuggestion.user_id == user_id)
        .order_by(UpdateSuggestion.created_at.desc())
    )
    if suggestion_type is not None:
        stmt = stmt.where(UpdateSuggestion.suggestion_type == suggestion_type)
    if status is not None:
        stmt = stmt.where(UpdateSuggestion.status == status)
    if target_role_id is not None:
        stmt = stmt.where(UpdateSuggestion.target_role_id == target_role_id)

    result = await session.execute(stmt)
    suggestions = result.scalars().all()
    return [_to_response(s) for s in suggestions]


async def accept_suggestion(
    session: AsyncSession,
    user_id: uuid.UUID,
    suggestion_id: uuid.UUID,
    notes: str | None = None,
) -> SuggestionResponse | None:
    """Accept a suggestion and update its status."""
    stmt = select(UpdateSuggestion).where(
        UpdateSuggestion.id == suggestion_id,
        UpdateSuggestion.user_id == user_id,
    )
    result = await session.execute(stmt)
    suggestion = result.scalar_one_or_none()
    if suggestion is None:
        return None

    suggestion.status = "accepted"
    suggestion.updated_at = datetime.now(timezone.utc)
    await session.flush()
    await session.refresh(suggestion)
    return _to_response(suggestion)


async def reject_suggestion(
    session: AsyncSession,
    user_id: uuid.UUID,
    suggestion_id: uuid.UUID,
    notes: str | None = None,
) -> SuggestionResponse | None:
    """Reject a suggestion and update its status."""
    stmt = select(UpdateSuggestion).where(
        UpdateSuggestion.id == suggestion_id,
        UpdateSuggestion.user_id == user_id,
    )
    result = await session.execute(stmt)
    suggestion = result.scalar_one_or_none()
    if suggestion is None:
        return None

    suggestion.status = "rejected"
    suggestion.updated_at = datetime.now(timezone.utc)
    await session.flush()
    await session.refresh(suggestion)
    return _to_response(suggestion)
