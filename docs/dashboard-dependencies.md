# Dipendenze dashboard

Stato: richieste di integrazione, 2026-10-31. Owner: 🛠 Luca.

La dashboard non crea una seconda persistenza. Consuma un `DashboardReadModel` tramite endpoint HTTP read-only; l’adapter vuoto attuale espone esplicitamente dati non disponibili.

## Richieste all’integratore DB

1. Esporre uno snapshot coerente con `observed_at`, `source` e `freshness`.
2. Fornire portfolio snapshot, cash, equity, posizioni e ordini già deduplicati/provenienti dal read model persistente.
3. Restituire watchlist, eventi/trigger e stato ultimo run quando esistono; non riempire campi mancanti con valori demo.
4. Mantenere la scrittura, le migrazioni e la deduplicazione fuori da `interface/`.
5. Concordare endpoint/configurazione di avvio senza aggiungere dipendenze a `pyproject.toml` o `uv.lock` da questa chat.

## Contratto attuale verificato

- `GET /api/dashboard`: portfolio/read model JSON.
- `GET /api/control-surface`: osservazione di moduli, runtime, configurazione non sensibile ed eventi; non applica modifiche.
- `GET /api/health`: stato del processo e flag `read_only`.
- Nessun endpoint POST/PUT/PATCH/DELETE.
- `source: "not connected"` e `freshness: "not available"` indicano il caso senza DB.

## Limiti

Il server stdlib è un adapter locale di sviluppo, non un deployment persistente. Non verifica autenticazione broker, non invia ordini e non dichiara dati finanziari live.
