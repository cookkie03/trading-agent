from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Trading Agent Workspace")
INDEX = Path(__file__).with_name("dashboard.html")

@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    return INDEX.read_text(encoding="utf-8")

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "trading-agent-dashboard"}
