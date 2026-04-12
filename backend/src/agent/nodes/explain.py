"""Explain node — produces a human-readable summary of agent outputs."""

from __future__ import annotations

from src.agent.state import CareerAgentState


async def explain(state: CareerAgentState) -> dict:
    """Summarize the results of the pipeline in natural language.

    Sprint 3+ will wire this to an LLM call using the prompt from
    src/prompts/explain.py.
    """
    return {
        "agent_logs": state.get("agent_logs", []),
    }
