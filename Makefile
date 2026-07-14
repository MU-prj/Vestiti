# Camerino developer entrypoints.
# Requires: uv, pnpm, docker (for `make dev`).

COMPOSE := docker compose -f infra/docker-compose.yml

.PHONY: install dev down test test-py test-node lint format typecheck migrate ci

install: ## Install all dependencies (Python + Node)
	uv sync --all-packages
	pnpm install

dev: ## Start the full stack (postgres, redis, minio, api, worker, web)
	$(COMPOSE) up --build

down: ## Stop the full stack
	$(COMPOSE) down

test: test-py test-node ## Run all tests

test-py:
	uv run pytest

test-node:
	pnpm test

lint: ## Lint Python and TypeScript
	uv run ruff check .
	uv run ruff format --check .
	pnpm lint
	pnpm format:check

format: ## Auto-format Python and TypeScript
	uv run ruff check --fix .
	uv run ruff format .
	pnpm format

typecheck: ## Typecheck Python (mypy --strict) and TypeScript (tsc)
	uv run mypy apps packages
	pnpm typecheck

migrate: ## Apply database migrations (available from phase 1)
	uv run alembic -c apps/api/alembic.ini upgrade head

ci: lint typecheck test ## Everything CI runs, locally
