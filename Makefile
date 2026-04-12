.PHONY: help dev dev-backend dev-frontend test test-backend test-frontend lint lint-backend lint-frontend format db-migrate db-seed build clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Development ──────────────────────────────────────────

dev: ## Start all services (backend + frontend + postgres + redis)
	docker compose up -d postgres redis
	@echo "Waiting for database..."
	@sleep 2
	cd backend && uvicorn src.main:app --reload --port 8000 &
	cd frontend && npm run dev
	@wait

dev-backend: ## Start backend only
	docker compose up -d postgres redis
	@echo "Waiting for database..."
	@sleep 2
	cd backend && uvicorn src.main:app --reload --port 8000

dev-frontend: ## Start frontend only
	cd frontend && npm run dev

# ── Testing ───────────────────────────────────────────────

test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests
	cd backend && python -m pytest tests/ -v

test-frontend: ## Run frontend tests
	cd frontend && npm run test

# ── Linting & Formatting ─────────────────────────────────

lint: lint-backend lint-frontend ## Lint all code

lint-backend: ## Lint backend (ruff)
	cd backend && ruff check src/ tests/

lint-frontend: ## Lint frontend (eslint)
	cd frontend && npm run lint

format: ## Auto-format all code
	cd backend && ruff format src/ tests/
	cd frontend && npx prettier --write "src/**/*.{ts,tsx,css}"

# ── Database ──────────────────────────────────────────────

db-migrate: ## Run Alembic migrations
	cd backend && alembic upgrade head

db-downgrade: ## Rollback last migration
	cd backend && alembic downgrade -1

db-seed: ## Seed sample data
	cd backend && python -m scripts.seed

db-reset: ## Reset database (drop + recreate + migrate)
	cd backend && alembic downgrade base && alembic upgrade head

# ── Build ─────────────────────────────────────────────────

build: ## Production build (Docker image)
	docker build -t careeragent:latest .

build-frontend: ## Build frontend only
	cd frontend && npm run build

# ── Setup ─────────────────────────────────────────────────

setup: ## First-time setup
	pip install -e backend/
	cd frontend && npm install
	cp -n .env.example .env || true
	docker compose up -d postgres redis
	@sleep 3
	cd backend && alembic upgrade head
	@echo "Setup complete! Run 'make dev' to start."

clean: ## Remove build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/dist
