# ADR 0003 — SourceAdapter reali e strategia di test a fixture

- **Stato**: accettata
- **Data**: 2026-07-12
- **Fase**: 2

## Contesto

La fase 2 introduce gli adapter verso sorgenti prodotto reali: Shopify Storefront
API, feed Google Shopping (XML/TSV) e feed dei network affiliati (CSV/XML). Vincoli:
nessuna chiamata live in CI, nessuno scraping (hard invariant #1), tutti gli adapter
devono onorare lo stesso contratto `SourceAdapter` consumato dall'ingestion.

## Decisioni

### Fixture registrate con httpx.MockTransport, niente vcrpy

I test "VCR-style" replayano risposte registrate in `apps/api/tests/fixtures/`.
Per gli adapter HTTP si inietta un `httpx.AsyncClient` con `MockTransport` che
serve le fixture (per Shopify, con routing sul cursore GraphQL per testare la
paginazione). Alternativa scartata: `vcrpy` — una dipendenza in più per un
beneficio nullo finché le fixture sono costruite a mano; se in futuro registreremo
sessioni live reali, la si rivaluterà con un ADR.

### Contenuto dei feed dietro un loader iniettabile

`GoogleShoppingFeedAdapter` e `AffiliateFeedAdapter` ricevono un
`loader: async () -> str` con factory `from_content(...)` (test, file locali) e
`from_url(...)` (produzione, httpx). L'adapter non sa da dove arriva il feed:
stesso codice di parsing in test e in produzione.

### Record malformati: skip conteggiato, mai crash

Un record senza prezzo/brand/availability non deve abbattere l'intera ingestion:
gli adapter saltano il record e incrementano `skipped_records` (esposto e
asserito nei test). La validazione forte resta nel dominio (`Product.__post_init__`).

### Mapping affiliati come configurazione

Le colonne variano per network: `AffiliateFieldMapping` è un value object di
configurazione (preset `AWIN_MAPPING` incluso; CJ/Impact/Rakuten = nuovi preset,
zero codice). Il deep-link affiliato va in `Product.affiliate_url`, distinto dal
`product_url` del merchant: la disclosure (invariant #5) si aggancia lì.

### Contract-test unico per tutti gli adapter

`test_adapter_contract.py` è parametrizzato su un registro di factory (mock
compreso): ogni adapter deve produrre `Product` validi, attribuiti al proprio
`source_id`, con prezzo positivo, URL http(s), `raw` preservato e fetch
deterministico/ripetibile. Un nuovo adapter si aggiunge al registro e ottiene
il contratto gratis.

### Normalizzazione condivisa in `adapters/parsing.py`

`parse_price` accetta `"139.99 EUR"` e `"EUR 139.99"`; `parse_availability`
normalizza le varianti lessicali di Google (`in stock`, `out_of_stock`, ...);
`backorder` mappa su `preorder` (stato normalizzato più vicino: acquistabile ora,
spedito dopo).

## Conseguenze

- Gli adapter live richiedono solo credenziali via env (`SHOPIFY_STOREFRONT_TOKEN`,
  token affiliati): nessun segreto nel repo, mock in CI.
- Colore: i feed forniscono nomi ("white"), non hex; `color_primary` resta `None`
  negli adapter e il nome viaggia in `raw` — la mappatura nome→hex/Lab arriva con
  `packages/color` (fase 5).
- La fase 4 (watches) riuserà `fetch_products` per il re-fetch periodico senza
  modifiche agli adapter.
