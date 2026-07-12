# CLAUDE.md — Camerino

Guida operativa per lo sviluppo di Camerino. Prosa in italiano; identificatori, path,
docstring, branch, header dei commit, variabili d'ambiente e codice in inglese.

## Missione

Camerino unifica capi da più negozi online in un'unica collezione, con un layer di AI
styling personale: armocromia rigorosa (deterministica, CIELAB) + virtual try-on.
Il fossato tecnico è `packages/color` + il try-on, NON l'aggregazione.

## Vincoli invalicabili (mai negoziabili)

1. **Niente scraping in violazione di ToS.** Sorgenti prodotto solo da: feed ufficiali
   (Google Shopping XML/TSV), network affiliati (Awin/CJ/Impact/Rakuten), Shopify
   Storefront API, feed forniti dal merchant. Tutto passa da `SourceAdapter`.
2. **Nessun segreto nel repo.** Solo `.env.example` con placeholder. Gitleaks in CI.
3. **Foto utente = dato biometrico sensibile.** Cifratura at-rest, endpoint di
   cancellazione GDPR, retention minima, mai usate per training, consenso esplicito.
4. **Try-on solo sulla foto dell'utente stesso.** Output watermarkato + moderation gate.
5. **Disclosure affiliazione** sempre visibile dove compaiono link affiliati.
6. **Checkout = astrazione** (`CheckoutProvider`): deep-link oggi, UCP/ACP-ready domani.

Se una task richiede di violarli: fermarsi e scrivere `DECISION NEEDED:` nella PR.

## Comandi

```bash
make install    # uv sync + pnpm install
make dev        # docker compose up -d --build
make test       # pytest (coverage >= 85% su domain+color) + vitest
make lint       # ruff check/format + eslint + prettier
make typecheck  # mypy --strict + tsc --noEmit
make migrate    # alembic upgrade head (da fase 1)
make e2e        # playwright smoke (richiede stack attivo)
```

## Struttura

- `apps/api` — FastAPI (`camerino_api`); `apps/worker` — ARQ (`camerino_worker`);
  `apps/web` — Next.js 15 (`@camerino/web`).
- `packages/domain` (`camerino_domain`) — entità pure, I/O-free, coverage ≥ 85%.
- `packages/color` (`camerino_color`) — color science deterministica, nessuna API
  esterna nel path principale, coverage ≥ 85%.
- Workspace: uv (Python, venv unica a root) + pnpm (Node). Docker build sempre con
  context = root del repo.

## Convenzioni di lavoro

- Conventional Commits (`feat:`, `fix:`, `test:`, `chore:`, `docs:`, `refactor:`).
- TDD su domain, color e diff engine: prima il test, poi l'implementazione.
- ADR in `docs/adr/NNNN-*.md` per ogni decisione architetturale non banale.
- Nuove dipendenze solo se necessarie, introdotte con commit `chore(deps):`.
- CI verde a ogni push; ogni fase si chiude con PR mergeata e DoD verificata.
- Mock in CI: nessuna chiamata live a provider esterni nei test.

## Stato delle fasi

- [x] Fase 0 — Scaffolding & CI skeleton
- [x] Fase 1 — Dominio & ingestion normalizzata (Postgres, Alembic, MockAdapter, dedup)
- [ ] Fase 2 — SourceAdapter reali (Shopify, Google Shopping feed, affiliati) con mock in CI
- [ ] Fase 3 — Collections, Outfit & palette-coherence
- [ ] Fase 4 — Watches: restock & price-drop
- [ ] Fase 5 — Motore armocromia + ΔE (`packages/color`)
- [ ] Fase 6 — Virtual try-on (FASHN via fal.ai dietro interfaccia, mock in CI)
- [ ] Fase 7 — Frontend completo
- [ ] Fase 8 — Agentic-commerce readiness (CheckoutProvider, export feed UCP-readable)

## Decisioni prese

- Fase 0: uv al posto di poetry, gitleaks come binario in CI (niente
  gitleaks-action: richiede licenza per le org), `migrations.yml` skippa finché
  Alembic non esiste. Dettagli in `docs/adr/0001-monorepo-and-tooling.md`.
- Fase 1: identity key a precedenza fissa GTIN(14)→brand+MPN→brand+SKU→fuzzy
  (brand, titolo normalizzato, colore); canonical = primo visto, un'offer per
  (canonical, source); persistenza in `camerino_api.db` dietro il port
  `ProductStore`; worker dipende dal package `camerino-api`; test async con
  anyio; integrazione Postgres skippabile. Dettagli in
  `docs/adr/0002-domain-model-and-dedup.md`.
