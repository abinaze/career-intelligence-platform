.PHONY: help setup dev-up dev-down dev-logs build lint format type-check test test-backend test-frontend migrate migrate-create clean seed-db load-onet docker-build docker-up docker-down docker-logs

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Install all dependencies
	@echo "→ Installing root dependencies..."
	pnpm install
	@echo "→ Setting up Python virtual environment..."
	cd apps/backend && uv venv .venv && uv sync
	@echo "→ Setting up git hooks..."
	pnpm husky
	@echo "✓ Setup complete"

dev-up: ## Start Postgres + Redis only (run backend/frontend locally)
	docker compose -f infrastructure/docker/docker-compose.dev.yml up -d

dev-down: ## Stop Postgres + Redis
	docker compose -f infrastructure/docker/docker-compose.dev.yml down

dev-logs: ## Tail Postgres + Redis logs
	docker compose -f infrastructure/docker/docker-compose.dev.yml logs -f

docker-build: ## Build all app containers (backend, frontend, postgres, redis)
	docker compose -f infrastructure/docker/docker-compose.dev.yml build

docker-up: ## Start the full stack in containers (backend + frontend + db + redis)
	docker compose -f infrastructure/docker/docker-compose.dev.yml --profile full up -d

docker-down: ## Stop the full containerised stack
	docker compose -f infrastructure/docker/docker-compose.dev.yml --profile full down

docker-logs: ## Tail all container logs
	docker compose -f infrastructure/docker/docker-compose.dev.yml logs -f

build: ## Build all applications
	pnpm build

lint: ## Lint all code
	pnpm lint
	cd apps/backend && uv run ruff check .

format: ## Format all code
	pnpm format
	cd apps/backend && uv run ruff format .

type-check: ## Run type checkers
	pnpm type-check
	cd apps/backend && uv run mypy .

test: ## Run all tests
	pnpm --filter frontend test
	cd apps/backend && uv run pytest

test-backend: ## Run backend tests only
	cd apps/backend && uv run pytest -v

test-frontend: ## Run frontend tests only
	pnpm --filter frontend test

migrate: ## Run database migrations
	cd apps/backend && uv run alembic upgrade head

migrate-create: ## Create new migration (NAME=migration_name)
	cd apps/backend && uv run alembic revision --autogenerate -m "$(NAME)"

clean: ## Clean build artifacts
	find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name '.pytest_cache' -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name '.ruff_cache' -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name '.mypy_cache' -exec rm -rf {} + 2>/dev/null || true
	rm -rf apps/frontend/.next
	rm -rf apps/frontend/out
	@echo "✓ Clean complete"

seed-db: ## Seed database with initial data
	cd apps/backend && uv run python -m scripts.seed

load-onet: ## Load O*NET career taxonomy data and build the FAISS index
	cd apps/backend && uv run python -m src.scripts.load_onet
