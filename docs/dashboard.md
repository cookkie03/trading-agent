# Dashboard Trading Agent

Stato: MVP locale in implementazione/verifica, 2026-10-31.

## Scelta

La UI usa React + TypeScript + Vite/npm e legge contratti HTTP read-only dal backend Python. È una scelta deliberata rispetto alla prima indicazione Streamlit: separa il modulo sostituibile della UI dal backend e permette di distinguere HMR dal refresh dei dati.

## Moduli

- Control surface: osserva moduli, runtime, configurazione non sensibile ed eventi senza esporre mutazioni.
- Portfolio: disponibile solo quando il read model persistente è collegato.
- Cash, posizioni e ordini: stessi limiti del portfolio.
- Watchlist, eventi e stato run: vuoti se non forniti dalla sorgente.
- Decisioni, trigger e benchmark/alpha: rispettivamente non disponibili o Post-MVP; nessun numero demo viene mostrato come reale.

## Contratto e avvio

Il backend espone `GET /api/dashboard` e `GET /api/health` su loopback. Il launcher `scripts/run_dashboard.py` legge il database indicato da `TRADING_AGENT_DB` (default `data/trading-agent.db`) e mantiene uno stato esplicito vuoto se il file non esiste. Il frontend usa `VITE_API_BASE_URL` per il backend e aggiorna via polling; npm non rende i dati finanziari real-time.

Per sviluppo usare `./scripts/run_dashboard_dev.sh`: avvia il backend read-only senza Docker e usa `TRADING_AGENT_DB` (default `data/trading-agent.db`). Il frontend Vite resta separato e si avvia con `npm --prefix frontend run dev`.

Per deployment persistente/local-production usare `docker compose build && docker compose up -d`; il volume `trading-agent-data` conserva SQLite e il servizio resta read-only verso l'HTTP. Ingestion OpenBB e sync portfolio Alpaca sono sempre comandi espliciti separati e non partono automaticamente nel container.
