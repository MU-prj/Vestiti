# CAMERINO — Brief operativo

> **Modalità**: agente autonomo su repository GitHub, lavoro multi-sessione, CI-driven.
> **Convenzione lingua**: prosa/ADR/commit-body in italiano; *tutti* gli identificatori, path, docstring, nomi di branch, messaggi di commit (header conventional-commit), variabili d'ambiente e codice in inglese.
> **Regola d'oro**: ogni fase si chiude solo con **CI verde** e **una PR mergeata**. Niente fase considerata "done" senza test che la coprono.

## 1. Missione

Costruire **Camerino**: un "camerino digitale universale" che unifica capi da più negozi online in un'unica collezione, con sopra un layer di **AI styling personale** — armocromia rigorosa + virtual try-on — che è il vero elemento differenziante.

**One-liner**: *"Importa capi da qualsiasi negozio in un unico guardaroba, scopri la tua palette armocromatica, e vediti addosso l'outfit prima di comprarlo."*

Il differenziante NON è l'aggregazione (commodity). È **lo styling AI fatto con rigore di color science + try-on fotorealistico**.

## 2. Vincoli invalicabili (hard invariants)

1. **Niente scraping in violazione di ToS.** Sorgenti prodotto *solo* da: feed ufficiali (Google Shopping XML/TSV), network affiliati (Awin/CJ/Impact/Rakuten), Shopify Storefront API, o feed forniti dal merchant. Tutto passa da `SourceAdapter`; nessun HTML-scraping di siti retail.
2. **Nessun segreto nel repo.** Solo `.env.example` con placeholder. La CI ha un job gitleaks che fallisce se trova pattern di secret.
3. **Foto utente = dato biometrico.** Cifratura at-rest, endpoint di cancellazione GDPR, retention minima, mai usate per training, consenso esplicito prima dell'upload.
4. **Try-on solo sulla foto dell'utente stesso.** Output sempre watermarkato + moderation gate. Nessun try-on su foto di terzi.
5. **Disclosure affiliazione** sempre visibile dove compaiono link affiliati.
6. **Checkout = astrazione** (deep-link oggi, UCP/ACP-ready domani). Nessun pagamento reale.

Se una task richiede di violarli: fermati e scrivi `DECISION NEEDED:` nella PR.

## 3. Struttura del monorepo

```
apps/api      FastAPI backend        apps/worker  ARQ background jobs
apps/web      Next.js 15 frontend    packages/domain   entità pure, zero I/O
packages/color   armocromia + ΔE     packages/adapters interfacce verso l'esterno
packages/ui   componenti condivisi   infra/       docker-compose + riferimenti CI
```

**Stack**: Python 3.12 (uv workspace), FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, ARQ+Redis; Next.js 15, TS strict, Tailwind 4; PostgreSQL 16, Redis 7, MinIO.
**Qualità**: ruff + mypy --strict + pytest (coverage ≥85% su domain/color); eslint + prettier + tsc + vitest (+ playwright dalla Fase 7).
**Comandi**: `make install`, `make test`, `make lint`, `make typecheck`, `make dev` (compose), `make ci`.

## 4. Piano a fasi

| Fase | Contenuto | Stato |
| --- | --- | --- |
| 0 | Scaffolding monorepo + CI skeleton (lint/typecheck/test/gitleaks/build, e2e smoke) | ✅ completata |
| 1 | Dominio + ingestion + dedup `ProductIdentity` + Alembic + `migrations.yml` | ✅ completata |
| 2 | SourceAdapter reali (Shopify/GoogleShopping/Affiliate) su fixture, mock in CI | ⏳ |
| 3 | Collections, Outfit, palette-coherence, AffiliateUrlBuilder | ⏳ |
| 4 | Watches restock/price-drop + diff engine + Notifier | ⏳ |
| 5 | Motore armocromia + ΔE2000 + `POST /skin-profile` + ADR soglie | ⏳ |
| 6 | Virtual try-on (FASHN via fal.ai dietro `FAL_KEY`, mock in CI, watermark+moderation) | ⏳ |
| 7 | Frontend completo + playwright smoke | ⏳ |
| 8 | CheckoutProvider (deep-link attivo, stub UCP/ACP) + export feed UCP-readable | ⏳ |

Cross-cutting: logging strutturato, `/health` + `/ready`, endpoint GDPR, cifratura foto, rate limiting sul try-on.

## 5. Registro decisioni

Le decisioni architetturali non banali vivono in `docs/adr/`. Registro sintetico:

- **2026-07-14 — Branch di lavoro unico.** L'ambiente di esecuzione vincola lo sviluppo al branch `claude/camerino-wardrobe-dj2t6f` (niente branch `phase/NN-*`): le fasi sono serie di commit conventional-commit su questo branch, con PR verso `main`.
- **2026-07-14 — uv workspace + hatchling.** Monorepo Python come uv workspace (membri: apps/api, apps/worker, packages/domain|color|adapters), namespace package `camerino.*`. Pytest con `--import-mode=importlib` per evitare collisioni di moduli di test omonimi tra package.
- **2026-07-14 — gitleaks via CLI container.** In CI gitleaks gira come container ufficiale (`ghcr.io/gitleaks/gitleaks`) e non come `gitleaks-action` (che richiede licenza per le organizzazioni).
- **2026-07-14 — Dedup deterministico a 4 chiavi** (`gtin` → `brand_mpn` → `brand_sku` → `fuzzy` su forme normalizzate, con regola di conflitto sugli identificatori forti): vedi ADR 0001. Stessa semantica in memoria (`IdentityIndex`) e in SQL (`ingest_product`).
- **2026-07-14 — Test DB su SQLite, migrazioni su PostgreSQL.** I modelli usano `JSON().with_variant(JSONB, "postgresql")` così i test unit girano in-memory senza servizi; la reversibilità delle migrazioni Alembic è verificata contro Postgres reale in `migrations.yml`.
- **2026-07-14 — `.gitignore` riscritto.** Il template iniziale (LaTeX/venv) ignorava directory legittime come `lib/`; sostituito con regole specifiche per il monorepo.

## 6. Protocollo di autonomia

1. Una fase alla volta, in ordine; TDD su domain/color/diff-engine.
2. Commit piccoli, conventional (`feat:`, `fix:`, `test:`, `chore:`, `docs:`, `refactor:`); header in inglese, body in italiano dove utile.
3. CI verde a ogni push; se si rompe, il commit successivo la ripara.
4. `DECISION NEEDED:` in PR quando servono credenziali reali, giudizi legali, o trade-off non ovvi.
5. Ogni decisione architetturale → ADR in `docs/adr/NNNN-*.md` + riga nel registro qui sopra.
6. Nuove dipendenze solo se necessarie, introdotte con commit `chore(deps):`.
