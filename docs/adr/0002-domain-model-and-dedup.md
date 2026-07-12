# ADR 0002 — Modello di dominio, strategia di dedup e persistenza

- **Stato**: accettata
- **Data**: 2026-07-12
- **Fase**: 1

## Contesto

La fase 1 introduce il modello di dominio, l'ingestion normalizzata e la
deduplicazione cross-merchant: lo stesso capo venduto da più negozi deve collassare in
un `CanonicalProduct` con N `Offer`. Serve una strategia di matching deterministica,
testabile senza I/O, e una persistenza che la rispetti tra run successive.

## Decisioni

### Chiave di identità a precedenza fissa

`identity_key(product)` risolve, in ordine di confidenza decrescente:

1. **GTIN** — normalizzato a 14 cifre (`zfill`): GTIN-8/12/13/14 dello stesso articolo
   collidono sulla stessa chiave; separatori (spazi, trattini) rimossi; GTIN invalidi
   (lunghezza o caratteri) degradano alla regola successiva invece di fallire.
2. **(brand, MPN)** — brand e MPN `casefold()`.
3. **(brand, SKU)** — come sopra; lo SKU è affidabile solo entro lo stesso brand.
4. **Fuzzy (brand, titolo normalizzato, colore)** — titolo passato da
   `normalize_title` (casefold, punteggiatura/underscore → spazio singolo, trim,
   accenti preservati); colore = hex normalizzato o slot vuoto.

La chiave è un value object hashable (`IdentityKey(kind, value)`): il `kind` fa parte
della chiave, quindi regole diverse non collidono mai tra loro per costruzione.

### Rappresentante = primo visto

Il `CanonicalProduct` prende i dati descrittivi (titolo, descrizione, immagine) dal
primo prodotto visto per quella chiave; le sorgenti successive contribuiscono solo
offer. Alternativa scartata: merge euristico dei campi (più "furbo" ma non
deterministico e difficile da spiegare). Un'offer per (canonical, source): la
ricomparsa della stessa sorgente aggiorna prezzo/availability/last_seen_at.

### Persistenza in `apps/api`, dominio puro

- I modelli SQLAlchemy (`canonical_products`, `offers`) e Alembic vivono in
  `camerino_api.db`; il dominio espone solo il port `ProductStore` (Protocol).
  Il worker dipende dal package `camerino-api` per riusare store e ingestion:
  alternativa scartata `packages/db` separato — un package in più senza beneficio
  finché i consumatori sono due app dello stesso repo.
- `key_value` è la tupla della chiave serializzata con separatore `\x1f` (unit
  separator, mai presente nelle parti normalizzate) + unique su `(key_kind,
  key_value)`: l'unicità dell'identità è garantita dal DB, non solo dal codice.
- Un test in CI garantisce che `import camerino_domain` non carichi alcuna lib di
  infrastruttura (fastapi/sqlalchemy/httpx/arq/redis) usando un interprete pulito.

### Ingestion come servizio, dedup contro lo store

`IngestionService.ingest(adapter)` consulta lo store per chiave (non un indice in
memoria): il collasso funziona anche tra run e tra batch di sorgenti diverse. Il
`ProductDeduplicator` in-memory del dominio resta per usi puri (test, anteprime).

### Test async con anyio, integrazione skippabile

I test async usano il plugin pytest di `anyio` (già dipendenza transitiva di
Starlette): niente `pytest-asyncio` in più. I test d'integrazione Postgres girano
quando `DATABASE_URL` punta a un server raggiungibile (service container in CI) e
skippano in modo esplicito altrove.

## Conseguenze

- La fase 2 implementa gli adapter reali contro lo stesso port `SourceAdapter`
  (async iterator di `Product`): nessun cambiamento al pipeline.
- La regola fuzzy è volutamente conservativa (richiede stesso colore): meglio due
  canonical distinti che un merge sbagliato. Eventuali migliorie (similarità di
  titolo, soglie) passeranno da un nuovo ADR.
- `migrations.yml` ora esercita davvero upgrade → downgrade → upgrade a ogni PR.
