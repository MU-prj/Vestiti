# Workflow CI/CD

I workflow GitHub Actions reali vivono in [`.github/workflows/`](../../.github/workflows/):

- `ci.yml` — lint, typecheck, test, scansione segreti (gitleaks), build immagini Docker.
- `e2e.yml` — smoke test end-to-end contro lo stack `docker compose` con provider mock.
- `migrations.yml` — (dalla Fase 1) verifica che le migrazioni Alembic siano reversibili.

Questa directory esiste come riferimento/documentazione dell'infrastruttura CI,
come previsto dalla struttura del monorepo.
