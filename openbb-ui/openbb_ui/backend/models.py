from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class Portfolio:
    available: bool
    reason: str | None = None

@dataclass(frozen=True)
class DashboardSnapshot:
    source: str
    freshness: str
    portfolio: Portfolio
    watchlist: list[dict[str, Any]] = field(default_factory=list)
    observations: list[dict[str, Any]] = field(default_factory=list)
    modules: dict[str, str] = field(default_factory=dict)

class DashboardReadModel:
    def snapshot(self) -> DashboardSnapshot:
        raise NotImplementedError

class EmptyDashboardReadModel(DashboardReadModel):
    def snapshot(self) -> DashboardSnapshot:
        return DashboardSnapshot(
            source="not connected", freshness="not available",
            portfolio=Portfolio(False, "Database read model not connected"),
            modules={"openbb_api": "unreachable", "benchmark": "post-mvp"},
        )

class SqliteDashboardReadModel(DashboardReadModel):
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)

    def snapshot(self) -> DashboardSnapshot:
        if not self.db_path.exists():
            return EmptyDashboardReadModel().snapshot()
        try:
            with sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True) as db:
                rows = db.execute("SELECT symbol, metric, value, observed_at, source FROM observations ORDER BY observed_at DESC").fetchall()
        except (sqlite3.Error, OSError):
            return EmptyDashboardReadModel().snapshot()
        observations = [dict(zip(("symbol", "metric", "value", "observed_at", "source"), row)) for row in rows]
        freshness = observations[0]["observed_at"] if observations else "not available"
        return DashboardSnapshot(
            source=f"sqlite:{self.db_path}", freshness=freshness,
            portfolio=Portfolio(False, "Portfolio read model not connected"),
            observations=observations,
            modules={"openbb_api": "unreachable", "benchmark": "post-mvp"},
        )
