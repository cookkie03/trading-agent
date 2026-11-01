# Trading Agent

Project workspace directory for trading-agent.

## Dashboard locale

Avvia frontend React/Vite e backend Python read-only insieme dalla root del repository:

```bash
./run_dashboard.sh
```

Apri `http://localhost:5173`. Il backend è disponibile su `http://localhost:8000`.
Il launcher non avvia `openbb-ui`; per fermare entrambi i processi usa `Ctrl+C`.

Se è la prima esecuzione, installa prima le dipendenze frontend:

```bash
npm install --prefix frontend
```

Il frontend aggiorna il codice tramite Vite HMR e interroga il backend ogni 15 secondi. Questo refresh non implica che siano disponibili dati finanziari real-time.
