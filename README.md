# CareerAgent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Node 20+](https://img.shields.io/badge/Node-20+-339933?logo=node.js&logoColor=white)](https://nodejs.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen.svg)](https://github.com/your-username/CareerAgent/pulls)

**A long-term career asset management system for software engineers, powered by AI agents.**

CareerAgent is not a one-time resume builder. It is a continuously running system that transforms your real work achievements into role-customized resumes, skill gap analyses, and JD-tailored application materials -- all orchestrated by specialized AI agents.

---

## Features

### :dart: Multi-Role Career Management

Maintain independent career profiles for different job targets (Agent Developer, Algorithm Engineer, Backend Engineer, Quant Developer, etc.). Each role gets its own capability model, customized resume, and gap tracker. No more maintaining a single generic resume or scrambling to customize before each application.

### :rocket: Achievement-to-Resume Pipeline

Submit your real work accomplishments -- code you shipped, milestones you hit, problems you solved -- and the AI agent pipeline automatically analyzes them, identifies which target roles they fit best, and generates structured resume update suggestions with explanations. Your career assets accumulate continuously instead of being lost to memory.

### :chart_with_upward_trend: Intelligent Gap Analysis

Go beyond vague feelings of "I'm not ready." CareerAgent provides structured gap reports for each target role: what skills are missing, what skills you have but lack evidence for, what areas need deeper project experience, and a prioritized improvement plan with actionable steps. Gaps are automatically re-evaluated as new achievements flow in.

### :clipboard: JD-Driven Resume Customization

Paste a real job description and get a tailored resume in seconds. The system parses the JD, matches it against your career assets, and produces either a freshly generated resume or a fine-tuned version of an existing one. You receive an ability match score, a resume expression match score, and a clear recommendation on whether to apply now, tune first, or fill gaps before applying.

---

## Architecture

CareerAgent follows a **modular monolith** architecture with **agent-based workflow orchestration**.

### Agent System

Seven specialized AI agents work together through three core pipelines:

| Agent | Responsibility |
|-------|---------------|
| Achievement Analysis | Parse raw achievements into structured career assets |
| Role Matching | Match achievements to relevant target roles |
| Resume Update | Generate resume update suggestions per role |
| Gap Evaluation | Track and re-evaluate skill gaps |
| JD Parsing | Extract requirements, keywords, and style from job descriptions |
| JD Tailoring | Generate or fine-tune resumes for specific JDs |
| Explain | Translate agent decisions into human-readable explanations |

### Core Pipelines

```
Pipeline 1: Achievement Processing
  achievement -> [Analysis] -> [Role Matching] -> [Resume Update] + [Gap Eval] -> [Explain]

Pipeline 2: Role Initialization
  role input -> [Capability Modeling] -> [Resume Init] -> [Gap Eval] -> [Explain]

Pipeline 3: JD Tailoring
  JD text -> [JD Parsing] -> [JD Tailoring] -> [Match Scoring] -> [Explain]
```

All agent workflows are orchestrated through **LangGraph** with multi-provider LLM support (OpenAI, Anthropic, Google Gemini), allowing cost optimization by assigning the best model for each agent's task.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI |
| Agent Framework | LangGraph |
| LLM Providers | OpenAI, Anthropic, Google Gemini |
| Database | PostgreSQL |
| ORM & Migrations | SQLAlchemy 2.0, Alembic |
| Frontend | React 19, Vite, TypeScript |
| UI | Tailwind CSS, Shadcn UI |
| State Management | TanStack Query |
| Cache | Redis |
| Deployment | Docker, docker-compose |

---

## Quick Start

### Prerequisites

- **Python** 3.11 or higher
- **Node.js** 20 or higher
- **Docker** and **Docker Compose** (for PostgreSQL and Redis)
- **LLM API key** (at least one of OpenAI, Anthropic, or Google Gemini)

### Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/CareerAgent.git
   cd CareerAgent
   ```

2. **Configure environment variables**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your LLM API keys:

   ```env
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   GEMINI_API_KEY=...
   ```

3. **Start infrastructure services**

   ```bash
   docker-compose up -d
   ```

   This starts PostgreSQL and Redis.

4. **Start the backend**

   ```bash
   make dev-backend
   ```

   The API server runs at `http://localhost:8000`.

5. **Start the frontend**

   ```bash
   make dev-frontend
   ```

   The UI runs at `http://localhost:5173`.

Or start everything at once:

```bash
make dev
```

---

## Development Guide

### Make Commands

| Command | Description |
|---------|-------------|
| `make dev` | Start all services (backend + frontend + infrastructure) |
| `make dev-backend` | Start backend only (uvicorn with hot-reload) |
| `make dev-frontend` | Start frontend only (Vite dev server) |
| `make test` | Run all tests (backend + frontend) |
| `make test-backend` | Run backend tests only |
| `make test-frontend` | Run frontend tests only |
| `make lint` | Lint all code (ruff + eslint) |
| `make format` | Auto-format all code |
| `make db-migrate` | Run Alembic database migrations |
| `make db-seed` | Seed database with sample data |
| `make build` | Production build (frontend + backend Docker image) |

### Project Structure

```
CareerAgent/
├── backend/
│   ├── src/
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── api/                    # Route handlers (roles, resumes, achievements, gaps, jd)
│   │   ├── agent/                  # LangGraph agent layer
│   │   │   ├── graph.py            # Workflow graph definitions
│   │   │   ├── state.py            # TypedDict state schemas
│   │   │   ├── configuration.py    # Per-agent model selection
│   │   │   ├── nodes/              # Agent node implementations
│   │   │   └── tools/              # Agent-callable tools
│   │   ├── core/                   # Shared infrastructure (config, database, LLM)
│   │   ├── models/                 # SQLAlchemy ORM models (16 tables)
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   ├── prompts/                # Prompt templates per agent
│   │   └── services/               # Business logic layer
│   ├── tests/                      # Test suites (API, agent, services)
│   ├── alembic/                    # Database migrations
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/             # UI components (Shadcn, layout, shared)
│   │   ├── pages/                  # Page components (Dashboard, Roles, Achievements, etc.)
│   │   ├── hooks/                  # TanStack Query hooks
│   │   ├── lib/                    # API client and utilities
│   │   └── types/                  # TypeScript type definitions
│   └── package.json
├── docs/                           # Documentation
├── docker-compose.yml
├── Makefile
└── .env.example
```

### Frontend Pages

| Route | Page |
|-------|------|
| `/` | Dashboard |
| `/roles` | Role list |
| `/roles/:id` | Role detail (info, resume, gaps, achievements) |
| `/resumes/:id` | Resume editor with agent suggestions |
| `/achievements` | Achievement timeline and detail drawer |
| `/gaps` | Gap board (Not Started / In Progress / Completed) |
| `/jd-tailor` | JD customization stepper flow |
| `/suggestions` | Update suggestion center |

---

## Roadmap

### Sprint 1: Foundation (Week 1-2)

Project scaffold, Docker setup, database models, FastAPI route stubs, React app shell, CI pipeline, and basic Dashboard.

### Sprint 2: Role Management + Resume (Week 3-4)

Target role CRUD, role initialization workflow, resume skeleton generation, resume view/edit, and gap list display.

### Sprint 3: Achievement Pipeline (Week 5-6)

Achievement input, Achievement Analysis and Role Matching agents, Resume Update agent, update suggestion center, and resume version creation on accept.

### Sprint 4: Gap System + JD Tailoring (Week 7-8)

Gap board page, JD parsing and tailoring agents, match scoring, JD customization stepper, and application readiness recommendations.

### Sprint 5: Polish + Open Source Readiness (Week 9-10)

Version history and diff view, Explain agent integration, complete documentation, test coverage, production Docker setup, and performance optimization.

---

## Contributing

Contributions are welcome! Please read the [Contributing Guide](CONTRIBUTING.md) for details on the development workflow, coding standards, and pull request process.

If you have ideas, bug reports, or feature requests, feel free to [open an issue](https://github.com/your-username/CareerAgent/issues/new).

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) for agent workflow orchestration
- [FastAPI](https://fastapi.tiangolo.com/) for the async backend framework
- [Shadcn UI](https://ui.shadcn.com/) for accessible and customizable React components
- [TanStack Query](https://tanstack.com/query) for server-state management
- All LLM providers (OpenAI, Anthropic, Google) for powering the agent intelligence
