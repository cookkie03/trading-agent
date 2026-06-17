from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Optional

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    Integer,
    String,
    UniqueConstraint,
    Index,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Cross-cutting: instrument registry
# ---------------------------------------------------------------------------
class Instrument(Base):
    """Tradeable instrument (the investable universe + held tickers)."""

    __tablename__ = "instruments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    sector: Mapped[Optional[str]] = mapped_column(String(128), default=None)
    asset_type: Mapped[str] = mapped_column(String(32), default="stock")
    asset_class: Mapped[Optional[str]] = mapped_column(String(32), default=None)  # e.g. us_equity
    exchange: Mapped[Optional[str]] = mapped_column(String(64), default=None)
    currency: Mapped[Optional[str]] = mapped_column(String(8), default=None)
    # Investable-universe bookkeeping (reconciled against the broker).
    tradable: Mapped[bool] = mapped_column(default=False)
    active: Mapped[bool] = mapped_column(default=True)   # False = delisted/removed at broker
    is_sp500: Mapped[bool] = mapped_column(default=False)  # benchmark constituent (seed)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ---------------------------------------------------------------------------
# Funnel: the persistent per-ticker "scheda"
# ---------------------------------------------------------------------------
class TickerCard(Base):
    """Persistent per-ticker card (parallelism-design B/C).

    Holds the cheap screening score (written by the deterministic screening
    module) and the latest synthesised evaluation (written by the deep-dive
    subgraph). The priority queue reads ``screening_score`` to decide which
    tickers deserve a deep dive. This is *not* the working ``research_state``:
    it is the durable summary that always lives in the DB.
    """

    __tablename__ = "ticker_card"

    symbol: Mapped[str] = mapped_column(String(32), primary_key=True)
    # Screening (E) — written by the deterministic Quick Thinker
    screening_score: Mapped[Optional[float]] = mapped_column(Float, default=None)
    rank: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    last_screened_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None
    )
    screening_signals: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, default=None)
    # Latest deep-dive evaluation — written by the PM after a deep dive (A)
    latest_direction: Mapped[Optional[str]] = mapped_column(String(16), default=None)
    latest_conviction: Mapped[Optional[str]] = mapped_column(String(16), default=None)
    latest_summary: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, default=None)
    next_check_date: Mapped[Optional[date]] = mapped_column(Date, default=None)
    in_portfolio: Mapped[bool] = mapped_column(default=False)
    # Dynamic watchlist membership (the working set under active analysis).
    in_watchlist: Mapped[bool] = mapped_column(default=False)
    watchlist_reason: Mapped[Optional[str]] = mapped_column(String(64), default=None)
    watchlist_added_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None
    )
    last_evaluated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


# ---------------------------------------------------------------------------
# Funnel: per-ticker important dates -> feed the Trigger Engine (DB-first hub)
# ---------------------------------------------------------------------------
class TickerEvent(Base):
    """A dated event for a ticker that deterministically wakes the system.

    Generalises ``ticker_card.next_check_date``: earnings, ex-dividend, a
    scheduled review, or a custom checkpoint. The Trigger Engine queries the
    due ones each cycle, so the system self-schedules from its own state.
    """

    __tablename__ = "ticker_events"
    __table_args__ = (
        UniqueConstraint("symbol", "date", "type", name="uq_ticker_event"),
        Index("ix_ticker_events_date", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    date: Mapped[date] = mapped_column(Date)
    type: Mapped[str] = mapped_column(String(24))  # earnings | exdiv | review | custom
    note: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    source: Mapped[Optional[str]] = mapped_column(String(32), default=None)
    consumed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
