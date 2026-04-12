"""Agent configuration — model assignments per agent node.

Each constant maps a node name to its preferred LLM model identifier.
The core/llm module resolves these identifiers to provider-specific chat
model instances at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AgentConfiguration:
    """Defines which LLM model each agent node should use.

    Swap model names here to re-balance cost vs. quality without touching
    node implementation code.
    """

    achievement_analysis: str = "gpt-4o-mini"
    role_matching: str = "gpt-4o-mini"
    resume_update: str = "claude-sonnet-4-20250514"
    gap_evaluation: str = "gpt-4o-mini"
    jd_parsing: str = "gpt-4o-mini"
    jd_tailoring: str = "claude-sonnet-4-20250514"
    resume_init: str = "claude-sonnet-4-20250514"
    explain: str = "gpt-4o-mini"


# Singleton used by nodes to look up their model assignment.
AGENT_CONFIGURATION = AgentConfiguration()
