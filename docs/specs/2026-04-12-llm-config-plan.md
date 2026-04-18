# LLM Config Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace hardcoded LLM config with a config.yaml + .env system that supports multiple providers per agent node.

**Architecture:** Two-layer config — a model registry (named models with provider/base_url/api_key/model) and an agents mapping (agent node name → model name). At runtime, `get_llm("agent_name")` resolves the chain: agent → model → provider → LangChain ChatModel instance.

**Tech Stack:** PyYAML, pydantic, langchain-openai (ChatOpenAI), langchain-anthropic (ChatAnthropic), python-dotenv (already via pydantic-settings)

---

### Task 1: Add PyYAML dependency and create config.yaml

**Files:**
- Modify: `backend/pyproject.toml`
- Create: `backend/config.yaml`
- Create: `backend/.env.example`

- [ ] **Step 1: Add pyyaml to pyproject.toml dependencies**

In `backend/pyproject.toml`, add `"pyyaml>=6.0"` to the `dependencies` list.

- [ ] **Step 2: Install the new dependency**

Run: `cd backend && pip install pyyaml>=6.0`

- [ ] **Step 3: Create config.yaml**

Create `backend/config.yaml`:

```yaml
# CareerAgent LLM Configuration
# API keys are referenced via ${ENV_VAR} syntax, resolved from .env / environment

models:
  glm-flash:
    provider: openai_compatible
    base_url: https://open.bigmodel.cn/api/paas/v4
    api_key: ${GLM_API_KEY}
    model: glm-4-flash
    temperature: 0.3

  claude-sonnet:
    provider: anthropic
    api_key: ${ANTHROPIC_API_KEY}
    model: claude-sonnet-4-20250514
    temperature: 0.3

agents:
  achievement_analysis: glm-flash
  role_matching: glm-flash
  resume_update: claude-sonnet
  gap_evaluation: glm-flash
  jd_parsing: glm-flash
  jd_tailoring: claude-sonnet
  resume_init: claude-sonnet
  capability_modeling: glm-flash
  explain: glm-flash
```

- [ ] **Step 4: Create .env.example**

Create `backend/.env.example`:

```bash
# LLM API Keys
GLM_API_KEY=your_glm_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/careeragent

# Redis
REDIS_URL=redis://localhost:6379/0

# LangSmith (optional)
LANGSMITH_API_KEY=
LANGSMITH_TRACING=false
LANGSMITH_PROJECT=careeragent

# App
APP_ENV=development
APP_PORT=8000
FRONTEND_URL=http://localhost:5173
```

- [ ] **Step 5: Commit**

```bash
git add backend/config.yaml backend/.env.example backend/pyproject.toml
git commit -m "feat: add config.yaml and .env.example for LLM configuration"
```

---

### Task 2: Rewrite llm.py with config-based factory

**Files:**
- Rewrite: `backend/src/core/llm.py`
- Create: `backend/tests/test_core/test_llm_config.py`

- [ ] **Step 1: Write tests for the config-based LLM factory**

Create `backend/tests/test_core/test_llm_config.py`:

```python
"""Tests for the config-based LLM factory."""

import os
from unittest.mock import patch

import pytest


def test_load_config_finds_file():
    """load_config should parse config.yaml and resolve env vars."""
    with patch.dict(os.environ, {"GLM_API_KEY": "test-key", "ANTHROPIC_API_KEY": "test-key2"}):
        from src.core.llm import load_config

        config = load_config()
        assert "models" in config
        assert "agents" in config
        assert config["models"]["glm-flash"]["api_key"] == "test-key"
        assert config["models"]["claude-sonnet"]["api_key"] == "test-key2"


def test_load_config_env_var_resolution():
    """${VAR} syntax should be resolved from environment."""
    with patch.dict(os.environ, {"MY_TEST_KEY": "resolved-value"}):
        from src.core.llm import _resolve_env_vars

        data = {"key": "${MY_TEST_KEY}", "nested": {"url": "http://${MY_TEST_KEY}/path"}}
        result = _resolve_env_vars(data)
        assert result["key"] == "resolved-value"
        assert result["nested"]["url"] == "http://resolved-value/path"


def test_load_config_missing_env_var_raises():
    """Missing env var should raise a clear error."""
    from src.core.llm import _resolve_env_vars

    with pytest.raises(ValueError, match="NONEXISTENT_KEY"):
        _resolve_env_vars({"key": "${NONEXISTENT_KEY}"})


def test_get_llm_unknown_agent_raises():
    """get_llm with unknown agent name should raise with helpful message."""
    with patch.dict(os.environ, {"GLM_API_KEY": "test", "ANTHROPIC_API_KEY": "test"}):
        from src.core.llm import get_llm

        with pytest.raises(ValueError, match="Unknown agent"):
            get_llm("nonexistent_agent")


def test_get_llm_returns_chat_model():
    """get_llm should return a ChatOpenAI instance for openai_compatible provider."""
    with patch.dict(os.environ, {"GLM_API_KEY": "test-key", "ANTHROPIC_API_KEY": "test-key"}):
        from src.core.llm import get_llm
        from langchain_openai import ChatOpenAI

        llm = get_llm("achievement_analysis")
        assert isinstance(llm, ChatOpenAI)


def test_get_llm_anthropic_provider():
    """get_llm should return a ChatAnthropic instance for anthropic provider."""
    with patch.dict(os.environ, {"GLM_API_KEY": "test", "ANTHROPIC_API_KEY": "test-key"}):
        from src.core.llm import get_llm
        from langchain_anthropic import ChatAnthropic

        llm = get_llm("resume_update")
        assert isinstance(llm, ChatAnthropic)


def test_default_config_when_file_missing():
    """When config.yaml is missing, embedded defaults should be used."""
    import src.core.llm as llm_mod

    original = llm_mod._CONFIG_PATH
    llm_mod._CONFIG_PATH = "/nonexistent/config.yaml"
    try:
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test"}):
            config = llm_mod.load_config()
            assert "models" in config
            assert "agents" in config
    finally:
        llm_mod._CONFIG_PATH = original
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_core/test_llm_config.py -v`
Expected: FAIL — `load_config`, `_resolve_env_vars` don't exist yet.

- [ ] **Step 3: Rewrite src/core/llm.py**

Replace the entire content of `backend/src/core/llm.py` with:

```python
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

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config.yaml"

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
        "resume_init": "default-openai",
        "capability_modeling": "default-openai",
        "explain": "default-openai",
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
                raise ValueError(
                    f"Environment variable ${var} referenced in config "
                    f"but not set. Set it in .env or your shell environment."
                )
            return val
        return _ENV_VAR_RE.sub(_replacer, obj)
    if isinstance(obj, dict):
        return {k: _resolve_env_vars(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_env_vars(v) for v in obj]
    return obj


def load_config() -> dict:
    """Load and resolve config.yaml. Falls back to embedded defaults."""
    if _CONFIG_PATH.exists():
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
        )

    raise ValueError(
        f"Unknown provider {provider!r} for model {model_name!r}. "
        f"Supported providers: openai_compatible, anthropic"
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_core/test_llm_config.py -v`
Expected: All 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/core/llm.py backend/tests/test_core/test_llm_config.py
git commit -m "feat: rewrite llm.py with config-driven factory + tests"
```

---

### Task 3: Update all agent nodes to use new get_llm API

**Files:**
- Modify: `backend/src/agent/nodes/achievement_analysis.py`
- Modify: `backend/src/agent/nodes/capability_modeling.py`
- Modify: `backend/src/agent/nodes/explain.py`
- Modify: `backend/src/agent/nodes/gap_evaluation.py`
- Modify: `backend/src/agent/nodes/jd_parsing.py`
- Modify: `backend/src/agent/nodes/jd_tailoring.py`
- Modify: `backend/src/agent/nodes/resume_init.py`
- Modify: `backend/src/agent/nodes/resume_update.py`
- Modify: `backend/src/agent/nodes/role_matching.py`

- [ ] **Step 1: Update achievement_analysis.py**

Find lines 44-47 (inside the try block):
```python
        from src.agent.configuration import AGENT_CONFIGURATION
        from src.core.llm import get_llm

        llm = get_llm("openai", AGENT_CONFIGURATION.achievement_analysis)
```
Replace with:
```python
        from src.core.llm import get_llm

        llm = get_llm("achievement_analysis")
```

- [ ] **Step 2: Update capability_modeling.py**

Find lines 61-64:
```python
        from src.agent.configuration import AGENT_CONFIGURATION
        from src.core.llm import get_llm

        llm = get_llm("openai", AGENT_CONFIGURATION.resume_init)
```
Replace with:
```python
        from src.core.llm import get_llm

        llm = get_llm("capability_modeling")
```

- [ ] **Step 3: Update explain.py**

Find lines 53-56:
```python
        from src.agent.configuration import AGENT_CONFIGURATION
        from src.core.llm import get_llm

        llm = get_llm("openai", AGENT_CONFIGURATION.explain)
```
Replace with:
```python
        from src.core.llm import get_llm

        llm = get_llm("explain")
```

- [ ] **Step 4: Update gap_evaluation.py (2 occurrences)**

First occurrence, find lines 120-123:
```python
        from src.agent.configuration import AGENT_CONFIGURATION
        from src.core.llm import get_llm

        llm = get_llm("openai", AGENT_CONFIGURATION.gap_evaluation)
```
Replace with:
```python
        from src.core.llm import get_llm

        llm = get_llm("gap_evaluation")
```

Second occurrence, find lines 221-224:
```python
        from src.agent.configuration import AGENT_CONFIGURATION
        from src.core.llm import get_llm

        llm = get_llm("openai", AGENT_CONFIGURATION.gap_evaluation)
```
Replace with:
```python
        from src.core.llm import get_llm

        llm = get_llm("gap_evaluation")
```

- [ ] **Step 5: Update jd_parsing.py**

Find lines 47-50:
```python
        from src.agent.configuration import AGENT_CONFIGURATION
        from src.core.llm import get_llm

        llm = get_llm("openai", AGENT_CONFIGURATION.jd_parsing)
```
Replace with:
```python
        from src.core.llm import get_llm

        llm = get_llm("jd_parsing")
```

- [ ] **Step 6: Update jd_tailoring.py**

Find lines 103-106:
```python
        from src.agent.configuration import AGENT_CONFIGURATION
        from src.core.llm import get_llm

        llm = get_llm("openai", AGENT_CONFIGURATION.jd_tailoring)
```
Replace with:
```python
        from src.core.llm import get_llm

        llm = get_llm("jd_tailoring")
```

- [ ] **Step 7: Update resume_init.py**

Find lines 57-60:
```python
        from src.agent.configuration import AGENT_CONFIGURATION
        from src.core.llm import get_llm

        llm = get_llm("openai", AGENT_CONFIGURATION.resume_init)
```
Replace with:
```python
        from src.core.llm import get_llm

        llm = get_llm("resume_init")
```

- [ ] **Step 8: Update resume_update.py**

Find lines 82-85:
```python
        from src.agent.configuration import AGENT_CONFIGURATION
        from src.core.llm import get_llm

        llm = get_llm("openai", AGENT_CONFIGURATION.resume_update)
```
Replace with:
```python
        from src.core.llm import get_llm

        llm = get_llm("resume_update")
```

- [ ] **Step 9: Update role_matching.py**

Find lines 72-75:
```python
        from src.agent.configuration import AGENT_CONFIGURATION
        from src.core.llm import get_llm

        llm = get_llm("openai", AGENT_CONFIGURATION.role_matching)
```
Replace with:
```python
        from src.core.llm import get_llm

        llm = get_llm("role_matching")
```

- [ ] **Step 10: Verify all changes compile**

Run: `cd backend && python -c "from src.core.llm import get_llm; print('OK')"`
Expected: `OK`

- [ ] **Step 11: Run ruff lint**

Run: `cd backend && ruff check src/agent/nodes/`
Expected: All checks passed

- [ ] **Step 12: Commit**

```bash
git add backend/src/agent/nodes/
git commit -m "refactor: update all agent nodes to use config-driven get_llm(agent_name)"
```

---

### Task 4: Delete old configuration module and clean up

**Files:**
- Delete: `backend/src/agent/configuration.py`
- Modify: `backend/src/core/config.py` (remove LLM-specific env vars — now in .env.example)

- [ ] **Step 1: Check no remaining imports of configuration.py**

Run: `cd backend && grep -r "from src.agent.configuration" src/ --include="*.py"`
Expected: No output (no remaining references).

- [ ] **Step 2: Delete configuration.py**

Run: `rm backend/src/agent/configuration.py`

- [ ] **Step 3: Clean up config.py — remove LLM-specific keys**

The `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` fields in `Settings` are no longer needed since API keys are now managed via config.yaml → .env. Remove these three fields from `backend/src/core/config.py`:

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/careeragent"
    REDIS_URL: str = "redis://localhost:6379/0"

    LANGSMITH_API_KEY: str = ""
    LANGSMITH_TRACING: bool = False
    LANGSMITH_PROJECT: str = "careeragent"

    APP_ENV: str = "development"
    APP_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5173"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
```

- [ ] **Step 4: Verify nothing in src/ references settings.OPENAI_API_KEY etc.**

Run: `cd backend && grep -r "settings.OPENAI_API_KEY\|settings.ANTHROPIC_API_KEY\|settings.GEMINI_API_KEY" src/ --include="*.py"`
Expected: No output.

- [ ] **Step 5: Run full test suite**

Run: `cd backend && python -m pytest tests/ -v`
Expected: All tests pass (8 tests total — 1 health check + 7 llm config).

- [ ] **Step 6: Commit**

```bash
git add -A backend/src/agent/configuration.py backend/src/core/config.py
git commit -m "refactor: delete hardcoded AgentConfiguration, remove LLM keys from Settings"
```

---

### Task 5: Add .env to .gitignore and verify end-to-end

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Ensure .env is gitignored**

Check if `backend/.env` is covered by existing `.gitignore`. The root `.gitignore` should already have entries. If not, add to root `.gitignore`:

```
# Environment files
.env
```

- [ ] **Step 2: Verify config.yaml loads correctly with env vars**

Run:
```bash
cd backend && GLM_API_KEY=test-glm ANTHROPIC_API_KEY=test-anthropic python -c "
from src.core.llm import get_llm, reload_config
reload_config()
llm = get_llm('jd_tailoring')
print(f'jd_tailoring: {type(llm).__name__} model={llm.model_name}')
llm2 = get_llm('achievement_analysis')
print(f'achievement_analysis: {type(llm2).__name__} model={llm2.model_name}')
"
```
Expected:
```
jd_tailoring: ChatAnthropic model=claude-sonnet-4-20250514
achievement_analysis: ChatOpenAI model=glm-4-flash
```

- [ ] **Step 3: Run full backend test suite**

Run: `cd backend && python -m pytest tests/ -v`
Expected: All tests pass.

- [ ] **Step 4: Run ruff on entire codebase**

Run: `cd backend && ruff check src/ tests/`
Expected: All checks passed.

- [ ] **Step 5: Commit if any gitignore change needed**

```bash
git add .gitignore
git commit -m "chore: ensure .env is gitignored"
```
