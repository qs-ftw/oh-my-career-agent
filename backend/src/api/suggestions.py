"""Suggestion endpoints — stubs returning mock data."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Path, Query

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
) -> list[SuggestionResponse]:
    """Return all suggestions, optionally filtered by type, status, or role."""
    return await suggestion_service.list_suggestions(
        suggestion_type=suggestion_type,
        status=status_filter,
        target_role_id=target_role_id,
    )


@router.post(
    "/{suggestion_id}/accept",
    response_model=SuggestionResponse,
    summary="Accept a suggestion",
)
async def accept_suggestion(
    suggestion_id: uuid.UUID = Path(..., description="The suggestion UUID"),
    body: SuggestionActionRequest | None = None,
) -> SuggestionResponse:
    """Mark a suggestion as accepted and apply the change."""
    notes = body.notes if body else None
    result = await suggestion_service.accept_suggestion(suggestion_id, notes=notes)
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
) -> SuggestionResponse:
    """Mark a suggestion as rejected."""
    notes = body.notes if body else None
    result = await suggestion_service.reject_suggestion(suggestion_id, notes=notes)
    if result is None:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return result
