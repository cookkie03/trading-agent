# Trading Agent

Progetto Python per un sistema multi-agente di analisi e gestione di un portafoglio azionario. Gli agenti elaborano informazioni e proposte; calcoli, controlli di rischio ed esecuzione restano deterministicamente verificabili.

## Development locale

Usa `.env` solo esplicitamente per i comandi che richiedono credenziali:

```bash
uv run --env-file .env python -m scripts.sync_portfolio \
  --database data/trading-agent.db
```

Dopo l'ingestion, materializza gli indicatori dalla outbox:

```bash
uv run --env-file .env python -m scripts.materialize_indicators \
  --database data/trading-agent.db \
  --window 20
```

Il worker è idempotente: ripetere il comando non duplica gli indicatori già materializzati. La dashboard legge solo derivati `ready` dal database; non calcola indicatori on-the-fly.

## Dashboard locale

Avvia frontend React/Vite e backend Python read-only insieme dalla root del repository:

```bash
./scripts/run_dashboard_dev.sh
```

Apri `http://localhost:5173`. Il backend è disponibile su `http://localhost:8000`.
Il launcher non avvia `openbb-ui`; per fermare entrambi i processi usa `Ctrl+C`.

Se è la prima esecuzione, installa prima le dipendenze frontend:

```bash
npm install --prefix frontend
```

Il frontend aggiorna il codice tramite Vite HMR e interroga il backend ogni 15 secondi. Questo refresh non implica che siano disponibili dati finanziari real-time.
