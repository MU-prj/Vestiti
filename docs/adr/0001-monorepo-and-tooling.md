# ADR 0001 — Monorepo, tooling e scheletro CI

- **Stato**: accettata
- **Data**: 2026-07-12
- **Fase**: 0

## Contesto

Camerino è un monorepo con backend Python (API + worker), frontend Next.js e due
pacchetti Python "puri" (`domain`, `color`) che costituiscono il fossato tecnico e
devono restare testabili al 100% senza I/O. Serve uno scheletro che renda la CI verde
dal primo giorno e imponga da subito i vincoli di qualità (mypy --strict, coverage,
secret scanning).

## Decisioni

### uv workspace invece di poetry

Il brief ammetteva `uv` o `poetry`. Scelto **uv**: un'unica venv a root per tutti i
membri (`apps/api`, `apps/worker`, `packages/domain`, `packages/color`), lockfile unico
(`uv.lock`), risoluzione e install molto più rapide in CI, supporto nativo alle
dipendenze tra membri del workspace (`[tool.uv.sources] ... = { workspace = true }`).
Poetry avrebbe richiesto un lockfile per pacchetto o plugin di terze parti per il
workspace. Il root è un pacchetto virtuale (`package = false`): ospita solo la
configurazione condivisa di ruff/mypy/pytest e il gruppo `dev`.

### Layout: `apps/` + `packages/`

- `packages/domain` e `packages/color` non hanno dipendenze da framework: la purezza è
  un vincolo architetturale (testabilità deterministica), non una preferenza.
- `apps/api` e `apps/worker` sono pacchetti separati che dipendono dai `packages/`;
  condividono la stessa immagine base Docker ma hanno Dockerfile e CMD distinti.
- Il frontend vive in `apps/web` sotto pnpm workspace; unico lockfile `pnpm-lock.yaml`.

### Coverage gate su domain + color

`pytest` gira dalla root con `--cov=camerino_domain --cov=camerino_color
--cov-fail-under=85`: la soglia dell'85% richiesta dal brief si applica ai due pacchetti
del fossato, non alle app (che hanno comunque test, ma dove la soglia rigida produrrebbe
solo rumore su glue code).

### Gitleaks come binario, non come action

`gitleaks/gitleaks-action@v2` richiede una licenza per i repository di organizzazioni.
Il job `secrets` scarica il binario a versione pinnata e lancia `gitleaks git . --redact`
su tutta la storia (checkout con `fetch-depth: 0`). Stesso hook anche in pre-commit.

### migrations.yml con skip esplicito

Il workflow di reversibilità (upgrade → downgrade → upgrade) esiste già ma esce con
successo e un messaggio chiaro finché `apps/api/alembic.ini` non compare (fase 1).
Alternativa scartata: aggiungere il workflow solo in fase 1 — preferito avere il
contratto CI completo visibile da subito.

### Next.js: build standalone

`output: "standalone"` in `next.config.ts` per un'immagine runtime minima (niente
`node_modules` completi nel container finale).

## Conseguenze

- Ogni nuovo pacchetto Python va aggiunto a `[tool.uv.workspace].members`, al Makefile
  (target `typecheck`) e ai `testpaths` di pytest.
- I Dockerfile si buildano sempre con context = root del repo (il lockfile del
  workspace riferisce tutti i membri).
- Node 20 in CI (baseline del brief) anche se in locale può girare Node 22.
