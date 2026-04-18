"""Interactive analysis endpoints — multi-turn conversational achievement enrichment."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user_id
from src.services import interactive_analysis_service

router = APIRouter(prefix="/achievements", tags=["interactive-analysis"])


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class ChatMessageResponse(BaseModel):
    reply: str
    questions: list[str]
    sufficiency: dict
    ready_to_generate: bool


class GenerateResponse(BaseModel):
    narrative: str
    bullets: list[str]
    tags: list[str]
    importance_score: float
    suggestions: list[dict]


@router.post(
    "/{achievement_id}/interactive/start",
    summary="Start interactive analysis session",
)
async def start_interactive(
    achievement_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
) -> ChatMessageResponse:
    """Start a new interactive analysis chat. AI reads existing content and asks first questions."""
    user_id = await get_current_user_id()
    result = await interactive_analysis_service.start_interactive_analysis(
        db, user_id, achievement_id
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Achievement not found")
    return result


@router.post(
    "/{achievement_id}/interactive/chat",
    summary="Send a message in interactive analysis",
)
async def send_chat(
    body: ChatMessageRequest,
    achievement_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
) -> ChatMessageResponse:
    """Send a user message and get AI's follow-up questions."""
    user_id = await get_current_user_id()
    result = await interactive_analysis_service.send_chat_message(
        db, user_id, achievement_id, body.message
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Achievement not found")
    return result


@router.post(
    "/{achievement_id}/interactive/generate",
    summary="Generate final polished content",
)
async def generate_final(
    achievement_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
) -> GenerateResponse:
    """Generate the final polished achievement from chat history."""
    user_id = await get_current_user_id()
    result = await interactive_analysis_service.generate_final_result(
        db, user_id, achievement_id
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Achievement not found")
    return result
