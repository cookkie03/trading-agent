# Trading Agent

Project workspace directory for trading-agent.

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
