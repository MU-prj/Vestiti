# Camerino

Il camerino digitale universale: importa capi da qualsiasi negozio online in un unico
guardaroba, scopri la tua palette armocromatica e vediti addosso l'outfit prima di comprarlo.

Il differenziante non è l'aggregazione: è lo **styling AI** fatto con rigore di color
science (armocromia deterministica in CIELAB, matching prodotti via ΔE2000) e il
**virtual try-on** fotorealistico.

## Struttura del monorepo

```
apps/
  api/      # FastAPI HTTP API
  worker/   # ARQ background worker (ingestion, watches, try-on jobs)
  web/      # Next.js 15 frontend
packages/
  domain/   # Entità di dominio pure, senza framework (I/O-free)
  color/    # Color science deterministica: armocromia 12 stagioni + ΔE2000
docs/adr/   # Architecture Decision Records
```

## Stack

- **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, ARQ + Redis
- **Frontend**: Next.js 15 (App Router), TypeScript strict, Tailwind
- **Data**: PostgreSQL 16, Redis 7, MinIO (S3-compatible)
- **Tooling**: uv (workspace Python), pnpm (workspace Node), ruff, mypy --strict,
  pytest, eslint, prettier, vitest, playwright

## Quickstart

Prerequisiti: [uv](https://docs.astral.sh/uv/), [pnpm](https://pnpm.io/), Docker.

```bash
cp .env.example .env   # mai committare .env con credenziali reali
make install           # uv sync + pnpm install
make dev               # docker compose up (postgres, redis, minio, api, worker, web)
make test              # pytest + vitest
make lint              # ruff + eslint + prettier
make typecheck         # mypy --strict + tsc --noEmit
```

- API: http://localhost:8000 (`/health`, `/ready`)
- Web: http://localhost:3000
- MinIO console: http://localhost:9001

## Convenzioni

Vedi [CLAUDE.md](CLAUDE.md) per convenzioni operative e vincoli di progetto, e
[docs/adr](docs/adr) per le decisioni architetturali.
