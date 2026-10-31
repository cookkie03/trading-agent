import os
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

ROOT = Path(__file__).parent
OPENBB_API_URL = os.getenv("OPENBB_API_URL", "http://localhost:6900").rstrip("/")

app = FastAPI(title="Trading Agent Workspace", version="0.1.0")


@app.get("/", response_class=HTMLResponse)
async def dashboard() -> str:
    return (ROOT / "dashboard.html").read_text(encoding="utf-8")


@app.get("/health")
async def health() -> dict[str, Any]:
    openbb = False
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            response = await client.get(f"{OPENBB_API_URL}/openapi.json")
            openbb = response.is_success
    except httpx.HTTPError:
        pass
    return {"status": "ok", "openbb": openbb, "openbb_url": OPENBB_API_URL}


@app.get("/api/openbb/{path:path}")
async def openbb_proxy(path: str) -> Any:
    """Read-only proxy for OpenBB API routes used by the dashboard."""
    if not path or path.startswith(("docs", "redoc", "openapi.json")):
        raise HTTPException(status_code=404, detail="Route not available through proxy")
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(f"{OPENBB_API_URL}/{path}")
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="OpenBB API is unavailable") from exc
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text[:500])
    return response.json()
