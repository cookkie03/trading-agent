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

Il backend espone `GET /api/dashboard` e `GET /api/health` su loopback. L’adapter iniziale `EmptyDashboardReadModel` serve per verificare UI, loading, errore e stato vuoto senza credenziali. Il frontend usa `VITE_API_BASE_URL` per il backend e aggiorna via polling; npm non rende i dati finanziari real-time.

Per i comandi esatti e la configurazione persistente vedere la sezione README che verrà integrata dalla chat principale; questa chat non modifica README.
