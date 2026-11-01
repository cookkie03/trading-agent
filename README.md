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

Le formule pure disponibili in `analysis/indicators.py` sono SMA, EMA, RSI Wilder, MACD, ATR Wilder e Pivot Points classici. Sono funzioni deterministiche testate, ma la pipeline di persistenza materializza attualmente solo SMA v1: l'estensione agli altri indicatori richiede la chiusura dei parametri MVP e delle relative versioni di formula.

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

## Ricerca semantica con MemPalace

MemPalace è una dipendenza runtime del progetto e usa il palace condiviso in
`/home/luca/.config/mempalace/palace`. Per verificare l'installazione e la ricerca:

```bash
uv run mempalace --version
uv run mempalace --palace /home/luca/.config/mempalace/palace status
uv run mempalace --palace /home/luca/.config/mempalace/palace search "query semantica"
claude mcp get mempalace
```

Il server MCP deve puntare a `mempalace-mcp --palace /home/luca/.config/mempalace/palace`.
La raccolta mantiene il repository principale e tutti i worktree Git registrati; prima di
rimuovere dati usare sempre `sync --dry-run` e verificare il report.
