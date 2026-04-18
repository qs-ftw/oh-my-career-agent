<div align="center">

# oh-my-career-agent

**AI-powered career asset management for software engineers.**

Not a one-time resume builder — a continuously running system that transforms
your real work achievements into role-customized resumes, skill gap analyses,
and JD-tailored application materials.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![React 19](https://img.shields.io/badge/React-19-61dafb?logo=react&logoColor=white)](https://react.dev/)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen.svg)](https://github.com/qs-ftw/oh-my-career-agent/pulls)

[中文文档](./README_CN.md) | **English**

</div>

---

## Why oh-my-career-agent?

You maintain multiple job targets. You accumulate work achievements daily. You need tailored resumes for each JD. But traditional tools treat these as disconnected tasks.

oh-my-career-agent connects them:

- **Long-term memory** — Maintain independent profiles for each target role. Assets accumulate over time.
- **Real achievement driven** — Every resume bullet traces back to real work. No fabrication.
- **Agent-powered, not template-powered** — 7 specialized AI agents analyze, match, score, and explain. Not keyword substitution.
- **Code-to-achievement** — Directly convert completed code work into career assets from your IDE.

## Features

### Multi-Role Career Management

Maintain separate career profiles for different job targets (Backend Engineer, AI Engineer, Full-Stack, etc.). Each role gets its own capability model, customized resume, and gap tracker.

### Achievement Pipeline

Submit work achievements and the AI agent pipeline automatically analyzes them, matches to target roles, and generates structured resume update suggestions. Assets accumulate continuously instead of being lost to memory.

### Code-to-Achievement (`/check-work`)

The killer feature for developers. Right in Claude Code, run `/check-work` after completing a coding task. The skill captures your git changes and conversation context, generates an achievement draft, runs deep analysis across four dimensions (technical, capability, project association, role matching), and publishes directly to your CareerAgent platform.

### Gap Analysis

Structured gap reports for each target role: what skills are missing, what lacks evidence, what needs deeper experience. Gaps re-evaluate automatically as new achievements flow in.

### JD-Driven Resume Customization

Paste a real JD and get a tailored resume. The system parses requirements, matches against your career assets, and produces a customized version with match scoring and application readiness recommendations.

## Architecture

```
                         ┌──────────────────────────┐
                         │      Frontend (React)      │
                         │  Dashboard / Roles / ...    │
                         └─────────────┬──────────────┘
                                       │ REST API
                         ┌─────────────▼──────────────┐
                         │      Backend (FastAPI)        │
                         │    API Routes / Services      │
                         └─────────────┬──────────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                         │                         │
    ┌─────────▼──────┐      ┌──────────▼──────────┐   ┌─────────▼──────┐
    │ Agent Layer     │      │   MCP Server         │   │   PostgreSQL   │
    │ (LangGraph)     │      │   (CareerAgent API)  │   │   + Redis      │
    │ 7 AI Agents     │      │   Claude Code tools   │   │                │
    └────────────────┘      └─────────────────────┘   └────────────────┘
```

### Three Entry Points

| Entry Point | How | Best For |
|---|---|---|
| **Web UI** | `http://localhost:5173` | Full management, dashboard, JD tailoring |
| **Claude Code Skill** | `/check-work` command | Converting code work into achievements |
| **MCP Server** | 8 tools via `.mcp.json` | Custom integrations and automation |

### Agent Pipelines

```
Pipeline 1: Achievement Processing
  achievement → Analysis → Role Matching → Resume Update + Gap Eval → Explain

Pipeline 2: Role Initialization
  role input → Capability Modeling → Resume Init → Gap Eval → Explain

Pipeline 3: JD Tailoring
  JD text → JD Parsing → JD Review → Keyword Extract → Resume Gen → Verify → Explain
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- At least one LLM API key (see Configuration below)

### Setup

```bash
# 1. Clone
git clone https://github.com/qs-ftw/oh-my-career-agent.git
cd oh-my-career-agent

# 2. Configure environment
cp .env.example .env
# Edit .env — fill in your API keys and database URL

# 3. Configure models
cp config.yaml config.yaml  # already provided, edit to match your providers
# See "Configuration" section below for details

# 4. Start infrastructure
docker compose up -d postgres redis

# 5. Start the app
make dev
```

The Web UI runs at `http://localhost:5173`. API docs at `http://localhost:8000/docs`.

## Configuration

The project uses two configuration files that work together:

### `.env` — Environment Variables

Holds secrets and infrastructure settings. Copy from `.env.example` and fill in:

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `GLM_API_KEY` | If using GLM models | ZhipuAI (BigModel) API key |
| `ANTHROPIC_API_KEY` | If using Claude models | Anthropic API key |
| `INFINI_API_KEY` | If using Infini models | Infini AI platform API key |
| `LANGSMITH_API_KEY` | No | LangSmith tracing key |
| `LANGSMITH_TRACING` | No | Enable agent tracing (`true`/`false`) |
| `APP_ENV` | No | `development` or `production` |
| `APP_PORT` | No | Backend port (default `8000`) |
| `FRONTEND_URL` | No | Frontend URL for CORS |

### `config.yaml` — Model & Agent Configuration

Controls which LLM models are available and which model each AI agent uses.

#### `models` section — Define LLM providers

Each entry defines a model you can reference later:

```yaml
models:
  my-glm:
    provider: openai_compatible    # "openai_compatible" or "anthropic"
    base_url: https://open.bigmodel.cn/api/paas/v4
    api_key: ${GLM_API_KEY}        # Resolved from .env
    model: glm-4-flash
    temperature: 0.3
```

| Field | Description |
|---|---|
| `provider` | `openai_compatible` (any OpenAI-compatible API) or `anthropic` |
| `base_url` | API endpoint (required for `openai_compatible`) |
| `api_key` | API key, supports `${ENV_VAR}` syntax to reference `.env` values |
| `model` | Model identifier as expected by the provider |
| `temperature` | Sampling temperature (0.0–1.0) |

The default config includes GLM, Infini Kimi, and Anthropic Claude models. Add or remove entries to match your available keys.

#### `agents` section — Assign models to agents

Maps each AI agent to a model name from the `models` section:

```yaml
agents:
  # Simple extraction/scoring — cheap & fast is enough
  achievement_analysis: glm-4.5-air
  gap_evaluation: glm-4.5-air

  # Complex generation — needs stronger reasoning
  jd_tailoring: glm-5-turbo
  resume_init: glm-5-turbo
  interactive_analysis: glm-5-turbo
```

**Available agents:**

| Agent | What it does | Recommended tier |
|---|---|---|
| `achievement_analysis` | Analyze work achievements | Light |
| `role_matching` | Match achievements to target roles | Light |
| `gap_evaluation` | Evaluate skill gaps | Light |
| `explain` | Generate explainable summaries | Light |
| `jd_parsing` | Parse job descriptions | Light |
| `capability_modeling` | Build role capability models | Light |
| `resume_update` | Generate resume update suggestions | Light |
| `resume_import` | Extract data from uploaded resumes | Light |
| `jd_keyword_extract` | Extract keywords from JD | Light |
| `project_selection` | Select projects for tailored resume | Light |
| `keyword_verification` | Verify keyword coverage | Light |
| `jd_tailoring` | Tailor resume to specific JD | Strong |
| `resume_init` | Generate initial resume skeleton | Strong |
| `resume_generation` | Generate full tailored resume | Strong |
| `interactive_analysis` | Deep coaching-style analysis | Strong |

**Tip:** Use cheaper/faster models for extraction and scoring tasks. Reserve powerful models for complex generation tasks like `jd_tailoring` and `interactive_analysis`.

### Enable `/check-work` in Claude Code

To convert code work into achievements from your IDE:

1. Install the MCP server dependencies:

```bash
cd mcp/careeragent-mcp && pip install -e . && cd ../..
```

2. The `.mcp.json` is already configured in the project root. Claude Code will auto-detect it.

3. Start the backend, then in Claude Code run:

```
/check-work
```

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI |
| Agent Framework | LangGraph |
| LLM Providers | OpenAI, Anthropic, Google Gemini |
| Database | PostgreSQL |
| Frontend | React 19, Vite, TypeScript |
| UI | Tailwind CSS, Shadcn UI |
| MCP Server | Python FastMCP, httpx |
| Deployment | Docker, docker-compose |

## Development

```bash
make dev              # Start all services
make dev-backend      # Backend only (uvicorn hot-reload)
make dev-frontend     # Frontend only (Vite dev server)
make test             # Run all tests
make lint             # Lint all code
make db-migrate       # Run database migrations
make db-seed          # Seed sample data
```

### Project Structure

```
oh-my-career-agent/
├── backend/                  # FastAPI backend
│   ├── src/
│   │   ├── api/              # REST route handlers
│   │   ├── agent/            # LangGraph agent layer (7 agents, 3 pipelines)
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # Business logic
│   │   └── core/             # Config, database, LLM, security
│   └── alembic/              # Database migrations
├── frontend/                 # React frontend
│   └── src/
│       ├── pages/            # Dashboard, Roles, Achievements, Gaps, JD Tailor
│       ├── components/       # Shadcn UI + custom components
│       └── hooks/            # TanStack Query hooks
├── mcp/careeragent-mcp/      # MCP Server for Claude Code
│   └── src/careeragent_mcp/
│       ├── server.py         # 8 MCP tools
│       └── client.py         # CareerAgent HTTP client
├── .claude/skills/check-work/  # /check-work skill definition
├── .mcp.json                 # MCP server registration
└── docs/                     # Design specs and plans
```

## Roadmap

- [x] Project scaffold, Docker setup, database models, CI pipeline
- [x] Role management, resume generation, gap tracking
- [x] Achievement pipeline (analysis, matching, suggestions)
- [x] JD tailoring pipeline (parsing, keyword extraction, customization)
- [x] MCP Server + `/check-work` skill for code-to-achievement conversion
- [ ] Interactive analysis (coaching-style achievement enrichment)
- [ ] PDF resume export
- [ ] Interview story bank (STAR+R structured preparation)
- [ ] Multi-user authentication

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](./CONTRIBUTING.md) for development workflow and PR process.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'feat: add some feature'`
4. Push the branch: `git push origin feature/your-feature`
5. Open a Pull Request

Bug reports and feature requests: [open an issue](https://github.com/qs-ftw/oh-my-career-agent/issues/new).

## License

[MIT](./LICENSE)

## Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) — Agent workflow orchestration
- [FastAPI](https://fastapi.tiangolo.com/) — Async Python web framework
- [Shadcn UI](https://ui.shadcn.com/) — Accessible React components
- [TanStack Query](https://tanstack.com/query/) — Server-state management
- [Model Context Protocol](https://modelcontextprotocol.io/) — MCP tool standard

---

<div align="center">

**If this project helps you, consider giving it a star.**

[⭐ Star on GitHub](https://github.com/qs-ftw/oh-my-career-agent)

</div>
