# LLM Configuration System Redesign

**Date**: 2026-04-12
**Status**: Approved

## Problem

Current LLM config is hardcoded in Python (`src/agent/configuration.py` dataclass + `src/core/llm.py` factory). All agent nodes hardcode `"openai"` as provider. No way to:
- Switch models per agent without editing code
- Use non-OpenAI providers (GLM, DeepSeek) for specific agents
- Configure base_url for OpenAI-compatible APIs
- Keep API keys out of config files

## Design

### Two-layer config: model registry + agent mapping

**`backend/config.yaml`** defines named models with full connection details, then maps each agent node to a model name.

```yaml
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

**`.env`** holds actual API keys, referenced via `${VAR}` syntax in config.yaml.

```bash
GLM_API_KEY=xxx
ANTHROPIC_API_KEY=xxx
```

### Provider types

Only two provider types needed:

| provider | LangChain class | Use for |
|---|---|---|
| `openai_compatible` | `ChatOpenAI` | OpenAI, GLM, DeepSeek, Qwen, Gemini (compat mode) — requires `base_url` |
| `anthropic` | `ChatAnthropic` | Claude series |

Adding a new provider type later is a single `elif` branch in the factory.

### Runtime resolution

```
config.yaml + .env
       |
  load_config()
  |- Parse YAML
  |- Recursively replace ${VAR} with os.environ[VAR]
  |- Pydantic validation
       |
  get_llm("jd_parsing")
  |- agents["jd_parsing"] -> "glm-flash"
  |- models["glm-flash"].provider -> "openai_compatible"
  |- -> ChatOpenAI(base_url=..., api_key=..., model=...)
  |- Return LangChain ChatModel instance
```

### Simplified API

Before (current):
```python
from src.core.llm import get_llm
from src.agent.configuration import AGENT_CONFIGURATION
llm = get_llm("openai", AGENT_CONFIGURATION.jd_tailoring)
```

After:
```python
from src.core.llm import get_llm
llm = get_llm("jd_tailoring")  # looks up agents mapping in config.yaml
```

## Files to change

| File | Action | Description |
|---|---|---|
| `backend/config.yaml` | **Create** | Model registry + agent mapping |
| `backend/.env.example` | **Create** | Example environment variables |
| `src/core/llm.py` | **Rewrite** | Config-based model factory |
| `src/agent/configuration.py` | **Delete** | Hardcoded config no longer needed |
| All 9 agent nodes in `src/agent/nodes/` | **Update** | Simplify `get_llm()` call |

## Validation

- config.yaml must parse and all `${VAR}` references must resolve
- Unknown agent names get a clear error with list of valid names
- Unknown model references in agents mapping get a clear error
- Missing API keys get a clear error identifying which model needs which env var
- Default config embedded in code as fallback when config.yaml missing
