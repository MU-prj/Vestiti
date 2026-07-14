# Camerino

*Importa capi da qualsiasi negozio in un unico guardaroba, scopri la tua palette
armocromatica, e vediti addosso l'outfit prima di comprarlo.*

**Camerino** è un camerino digitale universale: unifica capi da più negozi online in
un'unica collezione e ci costruisce sopra un layer di AI styling personale —
armocromia rigorosa (color science in spazio CIELAB, matching ΔE2000) e virtual
try-on fotorealistico.

## Architettura

Monorepo con workspace uv (Python) e pnpm (TypeScript):

| Path | Cosa contiene |
| --- | --- |
| `apps/api` | Backend FastAPI |
| `apps/worker` | Job in background (ARQ + Redis): ingestion, watch, try-on |
| `apps/web` | Frontend Next.js 15 (App Router) |
| `packages/domain` | Entità e logica di dominio pure, zero I/O |
| `packages/color` | Motore armocromia deterministico + matching ΔE |
| `packages/adapters` | `SourceAdapter`, `TryOnProvider`, `CheckoutProvider`, `Notifier` |
| `packages/ui` | Componenti React condivisi |
| `infra` | `docker-compose.yml` (postgres, redis, minio, api, worker, web) |

Le sorgenti prodotto arrivano **solo** da canali ufficiali (feed Google Shopping,
network affiliati, Shopify Storefront API, feed del merchant): nessuno scraping.
Le foto degli utenti sono trattate come dato biometrico: cifratura at-rest,
cancellazione GDPR, mai usate per training.

## Sviluppo

Prerequisiti: [uv](https://docs.astral.sh/uv/), [pnpm](https://pnpm.io/), Docker.

```bash
make install     # dipendenze Python + Node
make test        # pytest + vitest
make lint        # ruff + eslint + prettier
make typecheck   # mypy --strict + tsc
make dev         # docker compose: intero stack in locale
make ci          # tutto ciò che gira in CI, in locale
```

Copia `.env.example` in `.env` per la configurazione locale. Nessun segreto va
mai committato (la CI esegue gitleaks su tutta la history).

Il brief operativo completo, il piano a fasi e il registro delle decisioni sono in
[`CLAUDE.md`](CLAUDE.md); le ADR in [`docs/adr/`](docs/adr/).
