# CareerAgent Architecture Design Spec

**Date**: 2026-04-12
**Status**: Approved
**Scope**: MVP (Phase 1 - Personal Use)

## Context

CareerAgent is a long-term career asset management system for software engineers. Unlike one-time resume builders, it continuously converts real work achievements into role-customized resumes, gap analyses, and JD-tailored application materials — powered by an Agent system.

The MVP validates three core workflows: multi-role management, achievement-to-resume pipeline, and JD-specific resume customization.

## Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Backend | Python 3.11+ / FastAPI | Async API, LangGraph compatibility, rich AI ecosystem |
| Agent Framework | LangGraph | Workflow orchestration, state management, streaming |
| LLM | Multi-provider (OpenAI, Anthropic, Gemini) | Cost optimization per agent task, vendor independence |
| Database | PostgreSQL | Relational + JSONB, SaaS-ready, PRD requirement |
| ORM | SQLAlchemy 2.0 + Alembic | Type-safe models, production migrations |
| Frontend | React 19 + Vite + TypeScript | Fast DX, strong typing, reference project alignment |
| UI Library | Tailwind CSS + Shadcn UI | Consistent design, accessible components |
| State Management | TanStack Query | Server-state caching, optimistic updates |
| Deployment | Docker + docker-compose | Local dev and production parity |
| License | MIT | Permissive, open-source friendly |

## Project Structure

```
CareerAgent/
├── .github/                        # GitHub CI/CD & templates
│   ├── workflows/
│   │   ├── ci.yml                  # Lint, test, build on push/PR
│   │   └── release.yml             # Release & tag automation
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── dependabot.yml
├── backend/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry, CORS, lifespan
│   │   ├── api/                    # Route handlers
│   │   │   ├── __init__.py
│   │   │   ├── router.py           # Aggregate all sub-routers
│   │   │   ├── roles.py            # POST/GET/PATCH/DELETE /roles
│   │   │   ├── resumes.py          # GET/PATCH /resumes, versions
│   │   │   ├── achievements.py     # POST/GET /achievements, analyze
│   │   │   ├── gaps.py             # GET/PATCH /gaps
│   │   │   ├── jd.py               # POST /jd/parse, /jd/tailor
│   │   │   └── suggestions.py      # GET /suggestions, accept/reject
│   │   ├── agent/                  # LangGraph agent layer
│   │   │   ├── __init__.py
│   │   │   ├── graph.py            # Workflow graph definitions
│   │   │   ├── state.py            # TypedDict state schemas
│   │   │   ├── configuration.py    # Per-agent model selection
│   │   │   ├── nodes/              # Agent node implementations
│   │   │   │   ├── __init__.py
│   │   │   │   ├── achievement_analysis.py
│   │   │   │   ├── role_matching.py
│   │   │   │   ├── resume_update.py
│   │   │   │   ├── gap_evaluation.py
│   │   │   │   ├── jd_tailoring.py
│   │   │   │   ├── jd_parsing.py
│   │   │   │   ├── resume_init.py
│   │   │   │   └── explain.py
│   │   │   └── tools/              # Agent-callable tools
│   │   │       ├── __init__.py
│   │   │       ├── db_query.py     # Read career assets from DB
│   │   │       └── scoring.py      # Score calculations
│   │   ├── core/                   # Shared infrastructure
│   │   │   ├── __init__.py
│   │   │   ├── config.py           # Pydantic Settings from env
│   │   │   ├── database.py         # Async SQLAlchemy engine
│   │   │   ├── llm.py              # Multi-provider LLM abstraction
│   │   │   └── security.py         # Auth helpers (SaaS prep)
│   │   ├── models/                 # SQLAlchemy ORM models (16 tables)
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # DeclarativeBase + common mixins
│   │   │   ├── user.py             # users table
│   │   │   ├── workspace.py        # workspaces, workspace_members
│   │   │   ├── target_role.py      # target_roles, role_capability_models
│   │   │   ├── resume.py           # resumes, resume_versions
│   │   │   ├── achievement.py      # achievements, *_matches, *_links
│   │   │   ├── skill.py            # skill_entities
│   │   │   ├── gap.py              # gap_items
│   │   │   ├── jd.py               # jd_snapshots, jd_resume_tasks
│   │   │   └── agent.py            # agent_runs, update_suggestions
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── role.py
│   │   │   ├── resume.py
│   │   │   ├── achievement.py
│   │   │   ├── gap.py
│   │   │   ├── jd.py
│   │   │   └── suggestion.py
│   │   ├── prompts/                # Prompt templates per agent
│   │   │   ├── achievement_analysis.py
│   │   │   ├── role_matching.py
│   │   │   ├── resume_update.py
│   │   │   ├── gap_evaluation.py
│   │   │   ├── jd_tailoring.py
│   │   │   └── explain.py
│   │   └── services/               # Business logic (between API and models)
│   │       ├── __init__.py
│   │       ├── role_service.py
│   │       ├── resume_service.py
│   │       ├── achievement_service.py
│   │       ├── gap_service.py
│   │       ├── jd_service.py
│   │       └── suggestion_service.py
│   ├── tests/
│   │   ├── conftest.py             # Fixtures, test DB, async client
│   │   ├── test_api/               # API endpoint tests
│   │   ├── test_agent/             # Agent node tests
│   │   └── test_services/          # Service layer tests
│   ├── alembic/                    # Database migrations
│   │   ├── env.py
│   │   └── versions/
│   ├── alembic.ini
│   ├── pyproject.toml
│   └── langgraph.json
├── frontend/
│   ├── src/
│   │   ├── App.tsx                 # Router setup
│   │   ├── main.tsx                # Entry point
│   │   ├── global.css              # Tailwind imports
│   │   ├── components/
│   │   │   ├── ui/                 # Shadcn base components
│   │   │   ├── layout/             # Sidebar, Header, PageContainer
│   │   │   └── shared/             # ScoreCard, StatusBadge, etc.
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Roles.tsx
│   │   │   ├── RoleDetail.tsx
│   │   │   ├── ResumeDetail.tsx
│   │   │   ├── Achievements.tsx
│   │   │   ├── GapBoard.tsx
│   │   │   ├── JDTailor.tsx
│   │   │   └── Suggestions.tsx
│   │   ├── hooks/                  # TanStack Query hooks per domain
│   │   ├── lib/
│   │   │   ├── api.ts              # Axios/fetch API client
│   │   │   └── utils.ts            # Formatting, scoring helpers
│   │   └── types/                  # TypeScript type definitions
│   ├── components.json             # Shadcn UI config
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── index.html
├── docs/
│   ├── architecture.md
│   ├── api-reference.md
│   └── contributing.md
├── .gitignore
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── LICENSE                         # MIT
├── README.md                       # English (primary)
├── README_CN.md                    # Chinese
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── CHANGELOG.md
└── prd.md
```

## Agent Workflow Design

### Three Core Pipelines

#### Pipeline 1: Achievement Processing

Triggered when user submits a new achievement.

```
achievement_raw → [Achievement Analysis] → achievement_parsed
  → [Role Matching] → list[(role_id, match_score, reason)]
    → For each matched role (parallel):
        → [Resume Update] → suggestion(resume_update)
        → [Gap Evaluation] → suggestion(gap_update)
    → [Explain] → user-readable summary
```

LangGraph implementation:
- Linear chain for analysis + matching
- `Send()` for parallel branching per matched role
- Conditional edge: only process roles above match threshold
- All suggestions written to `update_suggestions` table
- User reviews and accepts/rejects via UI

#### Pipeline 2: Role Initialization

Triggered when user creates a new target role.

```
role_input → [Capability Modeling] → capability_model
  → [Resume Init] → resume_skeleton
  → [Gap Evaluation] → initial_gap_list
  → [Explain] → initialization summary
```

Linear chain. Creates `target_roles` + `role_capability_models` + `resumes` + initial `resume_versions` + `gap_items` in one transaction per step.

#### Pipeline 3: JD Tailoring

Triggered when user inputs a JD for customization.

```
jd_raw → [JD Parsing] → jd_parsed
  → [Mode branch]:
      Mode A (generate): Load all career assets → [JD Tailoring] → new_resume
      Mode B (tune): Load base_resume → [JD Tailoring] → tuned_resume
  → [Match Scoring] → {ability_score, resume_score, readiness}
  → [Explain] → recommendation + reasoning
```

### LangGraph State Schema

```python
class CareerAgentState(TypedDict):
    # Context
    user_id: str
    workspace_id: str

    # Achievement pipeline fields
    achievement_raw: Optional[str]
    achievement_parsed: Optional[dict]  # Structured achievement

    # Role init pipeline fields
    target_role_input: Optional[dict]
    capability_model: Optional[dict]

    # JD pipeline fields
    jd_raw: Optional[str]
    jd_parsed: Optional[dict]
    jd_mode: Optional[str]  # "generate_new" | "tune_existing"
    base_resume_id: Optional[str]

    # Shared outputs
    role_matches: Optional[list[dict]]
    suggestions: list[dict]
    gap_updates: list[dict]
    resume_draft: Optional[dict]
    match_scores: Optional[dict]

    # Audit trail
    agent_logs: list[dict]
```

### Multi-Provider LLM Strategy

Each agent node specifies its preferred model via `configuration.py`:

| Agent Node | Default Model | Rationale |
|-----------|--------------|-----------|
| Achievement Analysis | gpt-4o-mini | Structured extraction, cost-efficient |
| Role Matching | gpt-4o-mini | Classification task, fast |
| Resume Update | claude-sonnet-4-20250514 | Creative writing quality |
| Gap Evaluation | gpt-4o-mini | Logical analysis |
| JD Parsing | gpt-4o-mini | Extraction task |
| JD Tailoring | claude-sonnet-4-20250514 | Creative resume generation |
| Resume Init | claude-sonnet-4-20250514 | Template generation |
| Explain | gpt-4o-mini | Text summarization |

The `core/llm.py` module provides a unified interface. Agents call `get_llm(model_config)` and get a provider-agnostic chat model. Swapping providers changes only configuration, not agent code.

## Database Schema

16 tables organized in 5 domain groups. Follows PRD Section 21 with PostgreSQL-specific types.

### Key Schema Decisions

1. **JSONB for flexible fields**: `*_json` columns use JSONB for semi-structured data (capability models, parsed achievements, improvement plans)
2. **Soft delete**: `deleted_at` on `target_roles` and `resumes` for audit trail
3. **Version tracking**: `resume_versions` stores full content snapshots per version
4. **SaaS prep**: `workspace_id` and `user_id` on all data tables, even though MVP is single-user
5. **Audit trail**: `agent_runs` records every agent execution with inputs/outputs/explanations

### Migration Strategy

- Alembic manages all schema changes
- Each sprint starts with migration files for new tables/columns
- `make db-migrate` applies pending migrations
- `make db-seed` loads sample data for development

## Frontend Architecture

### Routing

```
/                    → Dashboard
/roles               → Role list
/roles/:id           → Role detail (tabs: info / resume / gaps / achievements)
/resumes/:id         → Resume detail (split-pane: content + suggestions)
/achievements        → Achievement list + detail drawer
/gaps                → Gap board (column view by status)
/jd-tailor           → JD customization (stepper flow)
/suggestions         → Update suggestion center
```

### Page Details

**Dashboard**: Stats cards (roles, resumes, gaps, achievements) + Role status cards + Recent activity feed

**Role Detail**: Tab-based — Basic Info / Resume Preview / Gap List / Related Achievements

**Resume Detail**: Two-column — Left: editable structured resume (Summary, Skills, Experience, Projects, Highlights, Metrics, Interview Points), Right: Agent suggestions panel with accept/reject buttons

**Achievement Center**: Timeline list with tag filters. Click to open detail drawer showing parsed results, matched roles, linked resumes

**Gap Board**: Three columns (Not Started / In Progress / Completed). Filter by role. Click gap to open detail drawer with explanation and improvement plan

**JD Tailor**: 4-step stepper — Input JD → Review parsed results → Choose mode (generate/tune) → View results (customized resume + scores + recommendation)

**Suggestions**: Filterable list — type (resume_update / gap_update / jd_tune), status (pending/accepted/rejected), source. Accept/reject inline.

### State Management

- **TanStack Query**: All server data. Custom hooks per domain (`useRoles`, `useResume`, `useAchievements`, etc.)
- **React state**: UI-only (filters, form state, modals, stepper progress)
- No global client state store needed.

## Development Workflow

### Commands

```bash
make dev            # Start all services (backend + frontend + postgres)
make dev-backend    # Backend only (uvicorn with hot-reload)
make dev-frontend   # Frontend only (vite dev server)
make test           # Run all tests (backend + frontend)
make test-backend   # Backend tests only
make test-frontend  # Frontend tests only
make lint           # Lint all code (ruff + eslint)
make format         # Auto-format all code
make db-migrate     # Run alembic migrations
make db-seed        # Seed sample data
make build          # Production build (frontend + backend docker)
```

### Environment

```env
# .env.example
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/careeragent
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
REDIS_URL=redis://localhost:6379

# LangSmith (optional)
LANGSMITH_API_KEY=...
LANGSMITH_TRACING=true
```

## Sprint Plan

### Sprint 1: Foundation (Week 1-2)

**Goal**: Project scaffold runs locally, database ready, CI green.

- Monorepo structure with all directories
- Docker compose (PostgreSQL + Redis)
- Makefile with all dev commands
- Backend: FastAPI app, all 16 SQLAlchemy models, Alembic migrations, all route stubs
- Frontend: Vite + React + Tailwind + Shadcn, routing setup, layout shell
- Open-source files: README (bilingual), LICENSE (MIT), CONTRIBUTING, CODE_OF_CONDUCT, CHANGELOG, .github templates, dependabot
- GitHub Actions CI: lint + test on push/PR
- Basic Dashboard page (static stats)

### Sprint 2: Role Management + Resume (Week 3-4)

**Goal**: Users can create roles, view auto-generated resumes and gaps.

- Target role CRUD API + UI
- Role initialization LangGraph workflow (capability modeling → resume skeleton → gap init)
- Resume view/edit API + UI
- Resume version recording
- Gap list display on role detail page

### Sprint 3: Achievement Pipeline (Week 5-6)

**Goal**: Users can submit achievements, get resume update suggestions.

- Achievement input API + UI
- Achievement Analysis Agent node
- Role Matching Agent node
- Resume Update Agent node
- Update suggestion center page (list + accept/reject)
- Gap Evaluation Agent node
- Achievement → Resume version creation on accept

### Sprint 4: Gap System + JD Tailoring (Week 7-8)

**Goal**: Full gap board and JD customization pipeline working.

- Gap board page (filter, sort, detail drawer)
- JD input + JD Parsing Agent node
- JD Tailoring Agent node (both modes)
- Match scoring logic
- JD customization page (full stepper flow)
- Investment recommendation output

### Sprint 5: Polish & Open Source Readiness (Week 9-10)

**Goal**: Production-quality, well-documented, open-source ready.

- Version history + diff view
- Explain Agent integration
- Complete bilingual README documentation
- API documentation (OpenAPI/Swagger)
- Test coverage improvement
- Docker production setup
- Performance review and optimization

## Verification Plan

1. **Sprint 1**: `make dev` starts all services, `make test` passes, database migrations run cleanly
2. **Sprint 2**: Create a role via UI → see auto-generated resume and gap list
3. **Sprint 3**: Submit achievement via UI → receive resume update suggestions → accept → see resume updated
4. **Sprint 4**: Input JD → get customized resume with scores and recommendation
5. **Sprint 5**: Full end-to-end flow works, all tests pass, README is complete

## Success Criteria (from PRD)

- Maintain 3+ target roles with independent resumes and gap lists
- Achievement submission produces credible update suggestions
- JD input generates usable customized resume with match assessment
- User can clearly see ability match and resume expression match scores
