# ADR 0001 — Strategia di dedup cross-merchant (`ProductIdentity`)

**Stato**: accettata · **Data**: 2026-07-14 · **Fase**: 1

## Contesto

Lo stesso capo compare su più negozi con listing diversi (titoli, prezzi, URL).
Camerino deve collassarli in un `CanonicalProduct` con N `Offer` ("one product,
many offers"), in modo **deterministico** e riproducibile in CI, sia in memoria
sia via SQL.

## Decisione

### Chiavi di identità, in ordine di forza

1. **`gtin`** — GTIN normalizzato a 14 cifre. La normalizzazione (`normalize_gtin`)
   accetta solo lunghezze GS1 valide (8/12/13/14 cifre), verifica il check digit
   mod-10 e fa zero-padding a 14. Un GTIN che non passa il checksum è scartato
   (nessuna chiave `gtin`), perché un identificatore corrotto è peggio di nessuno.
2. **`brand_mpn`** — brand normalizzato + MPN (lowercase). L'MPN è assegnato dal
   produttore, quindi stabile cross-merchant.
3. **`brand_sku`** — brand normalizzato + SKU (lowercase). Lo SKU è del merchant,
   ma nel fast-fashion coincide spesso con il codice articolo del produttore.
4. **`fuzzy`** — brand normalizzato + titolo normalizzato + bucket colore.

### Normalizzazione deterministica (niente edit-distance)

`normalize_brand`/`normalize_title`: NFKD + rimozione accenti, casefold,
rimozione punteggiatura, collasso whitespace. Il "fuzzy" matching è quindi una
**uguaglianza esatta su forme normalizzate**, non una similarità con soglia:
più conservativo (meno falsi merge) e totalmente riproducibile. Un matching a
similarità (es. token-set ratio) si può aggiungere in futuro come *candidato*
da confermare, mai come merge automatico.

Il colore entra nella chiave fuzzy come **bucket RGB grossolano** (4 livelli per
canale, 64 valori ciascuno): assorbe piccole differenze di encoding tra shop ma
separa colorway chiaramente diversi. `None` produce il bucket `"none"`.

### Regola di conflitto sugli identificatori forti

Un match su chiave debole è **rifiutato** se un identificatore più forte è
presente su entrambi i lati e diverge (`conflicts_on_stronger_key`): due listing
con GTIN validi diversi sono capi diversi anche con titolo identico; lo stesso
vale per l'MPN sotto un match `brand_sku`/`fuzzy`. Questo previene merge errati
tra taglie/colorway con GTIN distinti e titolo uguale.

### Apprendimento delle chiavi

Quando un prodotto viene fuso in un canonical, tutte le sue chiavi vengono
registrate sul canonical (senza sovrascrivere quelle esistenti): un canonical
nato senza GTIN diventa raggiungibile via GTIN appena un'offerta lo fornisce.

### Doppia implementazione, stessa semantica

- `IdentityIndex` (packages/domain): puro, in memoria, testato al 99%.
- `ingest_product` (apps/api): stesse funzioni chiave e stessa regola di
  conflitto, con lookup su colonne indicizzate (`gtin` UNIQUE, `brand_mpn_key`,
  `brand_sku_key`, `fuzzy_key`).

## Conseguenze

- Dedup riproducibile in CI senza servizi esterni; i test del DoD (collasso di
  due offer con lo stesso GTIN) girano sia sul dominio puro sia su SQLite.
- Capi identici senza alcun identificatore condiviso e con titoli diversi NON
  vengono uniti (falso negativo accettato: preferiamo due schede a un merge
  sbagliato).
- Il bucket colore a 4 livelli è una soglia documentata e rivedibile; cambiarla
  invalida le chiavi fuzzy esistenti (richiede re-ingestion, non migrazione).
