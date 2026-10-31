# Trading Agent Dashboard

Dashboard read-only locale per desktop e mobile. Il launcher verifica `/health`
prima di avviare il servizio, quindi il comando è sicuro da ripetere:

```bash
cd ~/trading-agent
./openbb-ui/openbb-ui
```

Aprire `http://localhost:8765`. La dashboard espone solo:

- `GET /` — interfaccia responsive;
- `GET /health` e `GET /api/health` — health check;
- `GET /api/dashboard` — read model;
- nessun endpoint mutante.

Il database e OpenBB non sono ancora collegati al read model: lo stato
`unreachable` o `not connected` è esplicito e non rappresenta dati simulati.
