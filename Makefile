.PHONY: dev dev-down test test-py test-web lint typecheck fmt migrate e2e install

install:
	uv sync --all-packages
	pnpm install

dev:
	docker compose up -d --build

dev-down:
	docker compose down

test: test-py test-web

test-py:
	uv run pytest

test-web:
	pnpm -r test

lint:
	uv run ruff check .
	uv run ruff format --check .
	pnpm -r lint
	pnpm -r format:check

typecheck:
	uv run mypy apps/api/src apps/api/tests apps/worker/src apps/worker/tests packages/domain/src packages/domain/tests packages/color/src packages/color/tests
	pnpm -r typecheck

fmt:
	uv run ruff format .
	uv run ruff check --fix .
	pnpm -r format

migrate:
	cd apps/api && uv run alembic upgrade head

e2e:
	pnpm --filter @camerino/web e2e
