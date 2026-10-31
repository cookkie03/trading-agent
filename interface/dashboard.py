"""Stable, read-only dashboard contract independent of storage and UI frameworks."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Protocol


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


class EmptyControlSurfaceReadModel:
    """Adapter sicuro finché runtime e configurazione non sono collegati."""

    def snapshot(self) -> ControlSurfaceSnapshot:
        return ControlSurfaceSnapshot.empty()
