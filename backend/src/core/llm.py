"""Config-driven LLM factory.

Loads model definitions and agent→model mappings from config.yaml.
API keys are resolved from environment variables via ${VAR} syntax.

Usage:
    from src.core.llm import get_llm
    llm = get_llm("jd_tailoring")  # returns ChatOpenAI or ChatAnthropic
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config.yaml"

_DEFAULT_CONFIG: dict = {
    "models": {
        "default-openai": {
            "provider": "openai_compatible",
            "api_key": "${OPENAI_API_KEY}",
            "model": "gpt-4o-mini",
            "temperature": 0.3,
        },
    },
    "agents": {
        "achievement_analysis": "default-openai",
        "role_matching": "default-openai",
        "resume_update": "default-openai",
        "gap_evaluation": "default-openai",
        "jd_parsing": "default-openai",
        "jd_tailoring": "default-openai",
        "jd_keyword_extract": "default-openai",
        "project_selection": "default-openai",
        "resume_generation": "default-openai",
        "keyword_verification": "default-openai",
        "resume_init": "default-openai",
        "capability_modeling": "default-openai",
        "explain": "default-openai",
        "resume_import": "default-openai",
        "interactive_analysis": "default-openai",
    },
}

_ENV_VAR_RE = re.compile(r"\$\{([^}]+)\}")


def _resolve_env_vars(obj):
    """Recursively replace ${VAR} strings with os.environ values."""
    if isinstance(obj, str):
        def _replacer(m):
            var = m.group(1)
            val = os.environ.get(var)
            if val is None:
                import logging
                logging.getLogger(__name__).warning(
                    f"Environment variable ${var} referenced in config but not set"
                )
                return m.group(0)  # leave ${VAR} as-is
            return val
        return _ENV_VAR_RE.sub(_replacer, obj)
    if isinstance(obj, dict):
        return {k: _resolve_env_vars(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_env_vars(v) for v in obj]
    return obj


def load_config() -> dict:
    """Load and resolve config.yaml. Falls back to embedded defaults."""
    if Path(_CONFIG_PATH).exists():
        with open(_CONFIG_PATH) as f:
            raw = yaml.safe_load(f)
    else:
        raw = _DEFAULT_CONFIG
    return _resolve_env_vars(raw)


# Cache resolved config at module level — loaded once per process.
_config: dict | None = None


def _get_config() -> dict:
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config() -> dict:
    """Force-reload config (useful after env changes in tests)."""
    global _config
    _config = load_config()
    return _config


# ---------------------------------------------------------------------------
# LLM factory
# ---------------------------------------------------------------------------

def get_llm(agent_name: str):
    """Return a LangChain ChatModel for the given agent node name.

    Resolves: agent_name → model_name → provider → ChatModel instance.

    Parameters
    ----------
    agent_name:
        An agent node name defined in config.yaml's ``agents`` section,
        e.g. "jd_tailoring", "achievement_analysis".

    Returns
    -------
    A langchain chat model instance ready for ``.invoke()`` / ``.ainvoke()``.
    """
    config = _get_config()

    # 1. Resolve agent → model name
    agents = config.get("agents", {})
    model_name = agents.get(agent_name)
    if model_name is None:
        valid = ", ".join(sorted(agents.keys()))
        raise ValueError(
            f"Unknown agent {agent_name!r}. "
            f"Valid agents: {valid}"
        )

    # 2. Resolve model name → model config
    models = config.get("models", {})
    model_cfg = models.get(model_name)
    if model_cfg is None:
        valid = ", ".join(sorted(models.keys()))
        raise ValueError(
            f"Agent {agent_name!r} references unknown model {model_name!r}. "
            f"Valid models: {valid}"
        )

    provider = model_cfg["provider"]
    model_id = model_cfg["model"]
    api_key = model_cfg.get("api_key", "")
    temperature = model_cfg.get("temperature", 0.3)

    # 3. Create provider-specific ChatModel
    if provider == "openai_compatible":
        from langchain_openai import ChatOpenAI

        kwargs = {
            "model": model_id,
            "temperature": temperature,
            "api_key": api_key or None,
            "max_retries": model_cfg.get("max_retries", 2),
        }
        if model_cfg.get("base_url"):
            kwargs["base_url"] = model_cfg["base_url"]
        return ChatOpenAI(**kwargs)

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=model_id,
            temperature=temperature,
            api_key=api_key or None,
            max_retries=model_cfg.get("max_retries", 2),
        )

    raise ValueError(
        f"Unknown provider {provider!r} for model {model_name!r}. "
        f"Supported providers: openai_compatible, anthropic"
    )
