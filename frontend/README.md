# Trading Agent cockpit

Read-only React + TypeScript + Vite frontend. Set `VITE_API_BASE_URL` to the local Python read-only server (default `http://localhost:8000`) and run `npm install && npm run dev`.

The dashboard polls every 15 seconds. This is a UI refresh interval, not a promise that any financial feed is real-time.
