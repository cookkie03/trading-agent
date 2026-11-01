# Persistenza SQLite MVP

**Stato: implementazione e verifica locale del 2026-10-31.** Questo modulo è la fondazione minima per un singolo servizio Python con scritture coordinate.

## Avvio e ispezione

Non serve un server database né una credenziale. Il gateway crea il file e applica le migrazioni quando viene aperto:

```python
from decimal import Decimal
from datetime import datetime, timezone
from storage import Observation, SQLiteDatabase

with SQLiteDatabase("data/trading.sqlite") as database:
    database.observations.save(
        Observation(
            source="vendor-a",
            external_id="quote-AAPL-2026-10-31T20:00:00Z",
            symbol="AAPL",
            metric="close",
            value=Decimal("189.01"),
            observed_at=datetime.now(timezone.utc),
            publication_date=datetime.now(timezone.utc),
            reference_date=datetime.now(timezone.utc),
            raw_payload='{"close":"189.01"}',
        )
    )
```

Per ispezionare il file senza modificarlo:

```bash
sqlite3 data/trading.sqlite '.schema'
sqlite3 data/trading.sqlite 'select source, external_id, symbol, metric, value from observations;'
```

## Contratto attuale

- `Observation` conserva valore come testo per non perdere cifre `Decimal`, timestamp normalizzati in UTC, `publication_date` e `reference_date`, payload grezzo e identificativo del record vendor.
- `(source, external_id)` è la chiave di deduplicazione. `save()` restituisce `True` quando inserisce e `False` quando il record esiste già; una ripetizione non aggiorna silenziosamente dati già persistiti.
- `SQLiteDatabase.transaction()` rende atomica una sequenza di scritture. Le query restano dentro il repository, non nei chiamanti.
- Lo schema è versionato tramite `PRAGMA user_version`; le migrazioni sono applicate all’apertura.
- `PriceBar` è il record OHLCV normalizzato: `symbol`, `interval`, timestamp, valori `Decimal`, `source`, `collected_at`, doppia data e payload raw. `MarketDataRepository` salva in modo idempotente sulla chiave `(symbol, interval, timestamp, source)` e legge finestre `[start, end)` ordinate per timestamp.
- La migrazione `002_create_price_bars` aggiunge la tabella e l’indice di lettura; l’adapter Yahoo resta nel package data e non viene duplicato nello storage.
- `scripts/ingest_market_data.py` è un runner guidato per OpenBB: adatta `data.models.PriceBar` al record storage e riporta inserimenti e duplicati per simbolo. `reference_date` usa il timestamp della barra; `publication_date` usa la data fornita dal provider oppure `collected_at`. La rete e le credenziali sono opt-in; i test del modulo usano un provider fake.

## Popolare il database con OpenBB

Il runner sincrono salva barre OHLCV normalizzate nel database SQLite e può essere rieseguito senza duplicare righe:

```bash
uv run python scripts/ingest_market_data.py AAPL \
  --start 2026-01-01T00:00:00+00:00 \
  --end 2026-11-01T00:00:00+00:00 \
  --database data/trading-agent.db
```

Il comando usa OpenBB con `yfinance` come provider predefinito. `source`, `collected_at`, `reference_date`, `publication_date` e `raw_payload` vengono conservati. La freshness non viene interpretata come dato live: per ora è rappresentata dal momento di raccolta.

## Confini e percorso PostgreSQL/TimescaleDB

SQLite è adeguato al perimetro MVP: un singolo host e un writer coordinato, senza avviare un servizio separato. Non è una promessa per più writer concorrenti, ingestione ad alto volume o retention time-series di produzione. Se il workload supera queste soglie, il passo successivo è un adapter PostgreSQL con migrazioni SQL revisionate; TimescaleDB potrà aggiungere hypertable e policy time-series sul lato PostgreSQL. Non basta cambiare una URL e SQLite non implementa TimescaleDB.

Il package non contiene chiamate vendor, cache, logica LLM o order execution. Il modello `Observation` è volutamente neutro e non sostituisce i contratti finanziari che verranno allineati con la chat vendor.
