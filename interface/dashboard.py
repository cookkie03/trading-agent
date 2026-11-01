"""Stable, read-only dashboard contract independent of storage and UI frameworks."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Protocol

from analysis.indicator_worker import SMA_FORMULA_VERSION, sma_parameters
from storage.sqlite import SQLiteDatabase


@dataclass(frozen=True)
class PortfolioReadModel:
    """Read model del portafoglio, senza operazioni di mutazione."""

    available: bool
    reason: str | None
    cash: str | None = None
    equity: str | None = None
    positions: list[dict[str, str]] = field(default_factory=list)
    orders: list[dict[str, str]] = field(default_factory=list)


@dataclass(frozen=True)
class DashboardSnapshot:
    """Snapshot coerente della dashboard a un singolo istante osservato."""

    observed_at: datetime
    source: str
    freshness: str
    portfolio: PortfolioReadModel
    watchlist: list[dict[str, str]] = field(default_factory=list)
    events: list[dict[str, str]] = field(default_factory=list)
    modules: dict[str, str] = field(default_factory=dict)

    @classmethod
    def empty(cls, *, observed_at: datetime | None = None) -> DashboardSnapshot:
        """Crea uno stato esplicito di indisponibilità, non dati simulati."""
        return cls(
            observed_at=observed_at or datetime.now(UTC),
            source="not connected",
            freshness="not available",
            portfolio=PortfolioReadModel(
                available=False,
                reason="Database read model not connected",
            ),
            modules={
                "decisions": "unavailable",
                "triggers": "unavailable",
                "benchmark": "post-mvp",
                "system_run": "unavailable",
            },
        )

    def to_dict(self) -> dict[str, object]:
        """Serializza lo snapshot mantenendo il timestamp in formato ISO-8601."""
        payload = asdict(self)
        payload["observed_at"] = self.observed_at.isoformat()
        return payload


@dataclass(frozen=True)
class ModuleStatus:
    name: str
    status: str
    last_run: str | None = None
    error_summary: str | None = None


@dataclass(frozen=True)
class ControlSurfaceSnapshot:
    """Snapshot del control plane; osserva lo stato ma non esegue comandi."""

    observed_at: datetime
    source: str
    freshness: str
    modules: list[ModuleStatus] = field(default_factory=list)
    runtime: dict[str, str] = field(default_factory=dict)
    config: dict[str, object] = field(default_factory=dict)
    events: list[dict[str, str]] = field(default_factory=list)

    @classmethod
    def empty(cls, *, observed_at: datetime | None = None) -> ControlSurfaceSnapshot:
        """Crea uno stato esplicito di indisponibilità del control plane."""
        return cls(
            observed_at=observed_at or datetime.now(UTC),
            source="not connected",
            freshness="not available",
            runtime={"status": "unavailable", "reason": "Control plane not connected"},
            config={"status": "unavailable", "reason": "Configuration read model not connected"},
        )

    def to_dict(self) -> dict[str, object]:
        """Serializza lo snapshot mantenendo il timestamp in formato ISO-8601."""
        payload = asdict(self)
        payload["observed_at"] = self.observed_at.isoformat()
        return payload


class DashboardReadModel(Protocol):
    def snapshot(self) -> DashboardSnapshot:
        """Restituisce una lettura coerente; non modifica lo stato."""
        ...


class ControlSurfaceReadModel(Protocol):
    def snapshot(self) -> ControlSurfaceSnapshot:
        """Restituisce solo lo stato del control plane; non esegue comandi."""
        ...


class EmptyDashboardReadModel:
    """Adapter sicuro finché il read model del database non è disponibile."""

    def snapshot(self) -> DashboardSnapshot:
        return DashboardSnapshot.empty()


class SQLiteDashboardReadModel:
    """Read-only dashboard adapter backed by persisted OHLCV bars."""

    def __init__(self, database_path: str | Path, *, symbols: tuple[str, ...] = ()) -> None:
        self._database_path = Path(database_path)
        self._symbols = tuple(symbol.upper() for symbol in symbols)

    def sma(
        self, symbol: str, *, window: int, interval: str = "1d"
    ) -> tuple[tuple[datetime, Decimal], ...]:
        """Calculate a read-only SMA from the persisted close prices."""
        if window <= 0:
            raise ValueError("window must be positive")
        if not self._database_path.exists():
            return ()
        with SQLiteDatabase(self._database_path) as database:
            values = database.indicators.get_ready(
                symbol.upper(),
                interval,
                "sma",
                sma_parameters(window),
                SMA_FORMULA_VERSION,
            )
        return tuple((value.timestamp, value.value) for value in values)

    def snapshot(self) -> DashboardSnapshot:
        if not self._database_path.exists():
            return DashboardSnapshot.empty()
        with SQLiteDatabase(self._database_path) as database:
            bars = self._latest_bars(database)
            portfolio = self._portfolio(database)
        if not bars and portfolio is None:
            return DashboardSnapshot.empty()
        latest_bar = max(bars, key=lambda bar: bar.collected_at) if bars else None
        portfolio_observed_at, portfolio_data = portfolio or (None, None)
        observed_at = max(
            (
                value
                for value in (
                    latest_bar.collected_at if latest_bar else None,
                    portfolio_observed_at,
                )
                if value is not None
            ),
        )
        return DashboardSnapshot(
            observed_at=observed_at,
            source="alpaca" if portfolio_data else latest_bar.source,
            freshness=observed_at.isoformat(),
            portfolio=portfolio_data
            or PortfolioReadModel(
                available=False,
                reason="Portfolio data not ingested",
            ),
            watchlist=[
                {
                    "symbol": bar.symbol,
                    "interval": bar.interval,
                    "timestamp": bar.timestamp.isoformat(),
                    "close": str(bar.close),
                    "volume": str(bar.volume),
                    "source": bar.source,
                    "collected_at": bar.collected_at.isoformat(),
                }
                for bar in bars
            ],
            modules={
                "market_data": "available",
                "decisions": "unavailable",
                "triggers": "unavailable",
                "benchmark": "post-mvp",
                "system_run": "unavailable",
            },
        )

    def _portfolio(self, database: SQLiteDatabase):
        latest = database.broker_snapshots.latest("alpaca")
        if latest is None:
            return None
        observed_at, payload = latest
        data = json.loads(payload)
        account = data["account"]
        return observed_at, PortfolioReadModel(
            available=True,
            reason=None,
            cash=account["cash"],
            equity=account["equity"],
            positions=data["positions"],
            orders=data["orders"],
        )

    def _latest_bars(self, database: SQLiteDatabase):
        symbols = self._symbols
        if not symbols:
            symbols = database.market_data.symbols()
        latest = []
        for symbol in symbols:
            bar = database.market_data.latest(symbol)
            if bar is not None:
                latest.append(bar)
        return tuple(latest)


class EmptyControlSurfaceReadModel:
    """Adapter sicuro finché runtime e configurazione non sono collegati."""

    def snapshot(self) -> ControlSurfaceSnapshot:
        return ControlSurfaceSnapshot.empty()
