"""Suggestion endpoints — database-backed list, accept, reject."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user_id
from src.schemas.suggestion import SuggestionActionRequest, SuggestionResponse
from src.services import suggestion_service

router = APIRouter(prefix="/suggestions", tags=["suggestions"])


@router.get(
    "",
    response_model=list[SuggestionResponse],
    summary="List suggestions",
)
async def list_suggestions(
    suggestion_type: str | None = Query(
        default=None, description="Filter by type, e.g. resume_update, gap_update"
    ),
    status_filter: str | None = Query(
        default=None, alias="status", description="Filter by status: pending/accepted/rejected"
    ),
    target_role_id: uuid.UUID | None = Query(
        default=None, description="Filter by target role"
    ),
    achievement_id: uuid.UUID | None = Query(
        default=None, description="Filter by source achievement"
    ),
    db: AsyncSession = Depends(get_db),
) -> list[SuggestionResponse]:
    """Return all suggestions, optionally filtered by type, status, role, or achievement."""
    user_id = await get_current_user_id()
    return await suggestion_service.list_suggestions(
        db, user_id,
        suggestion_type=suggestion_type,
        status=status_filter,
        target_role_id=target_role_id,
        achievement_id=achievement_id,
    )


@router.post(
    "/{suggestion_id}/accept",
    response_model=SuggestionResponse,
    summary="Accept a suggestion",
)
async def accept_suggestion(
    suggestion_id: uuid.UUID = Path(..., description="The suggestion UUID"),
    body: SuggestionActionRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> SuggestionResponse:
    """Mark a suggestion as accepted and apply the change."""
    user_id = await get_current_user_id()
    notes = body.notes if body else None
    result = await suggestion_service.accept_suggestion(db, user_id, suggestion_id, notes=notes)
    if result is None:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return result


@router.post(
    "/{suggestion_id}/reject",
    response_model=SuggestionResponse,
    summary="Reject a suggestion",
)
async def reject_suggestion(
    suggestion_id: uuid.UUID = Path(..., description="The suggestion UUID"),
    body: SuggestionActionRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> SuggestionResponse:
    """Mark a suggestion as rejected."""
    user_id = await get_current_user_id()
    notes = body.notes if body else None
    result = await suggestion_service.reject_suggestion(db, user_id, suggestion_id, notes=notes)
    if result is None:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return result
