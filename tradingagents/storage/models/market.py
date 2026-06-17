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
# Area: market_data (time-series) — TimescaleDB hypertable in production
# ---------------------------------------------------------------------------
class PriceBar(Base):
    """OHLCV bar. Carries the double date to prevent look-ahead bias.

    ``reference_date`` = the period the bar refers to; ``publication_date`` =
    when the datum became known to us. On PostgreSQL this table is promoted to
    a TimescaleDB hypertable on ``ts`` (see ``database.init_db``).
    """

    __tablename__ = "price_bars"
    __table_args__ = (
        UniqueConstraint("symbol", "ts", "interval", name="uq_price_bar"),
        Index("ix_price_bars_symbol_ts", "symbol", "ts"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    interval: Mapped[str] = mapped_column(String(8), default="1d")
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[Optional[float]] = mapped_column(Float, default=None)
    vendor: Mapped[Optional[str]] = mapped_column(String(32), default=None)
    reference_date: Mapped[Optional[date]] = mapped_column(Date, default=None)
    publication_date: Mapped[Optional[date]] = mapped_column(Date, default=None)
    inserted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ---------------------------------------------------------------------------
# Area: market_data — news (for the Market/Sentiment desks)
# ---------------------------------------------------------------------------
class NewsItem(Base):
    """A news/headline item for a ticker, with double date + optional sentiment."""

    __tablename__ = "news_items"
    __table_args__ = (
        Index("ix_news_symbol_ts", "symbol", "ts"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    headline: Mapped[str] = mapped_column(String(512))
    summary: Mapped[Optional[str]] = mapped_column(String(2048), default=None)
    source: Mapped[Optional[str]] = mapped_column(String(128), default=None)
    url: Mapped[Optional[str]] = mapped_column(String(1024), default=None)
    sentiment: Mapped[Optional[float]] = mapped_column(Float, default=None)
    dedup_key: Mapped[str] = mapped_column(String(512), index=True)
    vendor: Mapped[Optional[str]] = mapped_column(String(32), default=None)
    reference_date: Mapped[Optional[date]] = mapped_column(Date, default=None)
    publication_date: Mapped[Optional[date]] = mapped_column(Date, default=None)
    inserted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ---------------------------------------------------------------------------
# Area: market_data — social posts (Reddit/StockTwits/X), for the Sentiment desk
# ---------------------------------------------------------------------------
class SocialPost(Base):
    """A social/forum post for a ticker, with optional basic sentiment."""

    __tablename__ = "social_posts"
    __table_args__ = (
        Index("ix_social_symbol_ts", "symbol", "ts"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    platform: Mapped[str] = mapped_column(String(32))  # reddit / stocktwits / x
    body: Mapped[str] = mapped_column(String(2048))
    sentiment: Mapped[Optional[float]] = mapped_column(Float, default=None)  # +1/-1/0
    url: Mapped[Optional[str]] = mapped_column(String(1024), default=None)
    dedup_key: Mapped[str] = mapped_column(String(256), index=True)
    reference_date: Mapped[Optional[date]] = mapped_column(Date, default=None)
    publication_date: Mapped[Optional[date]] = mapped_column(Date, default=None)
    inserted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ---------------------------------------------------------------------------
# Area: market_data — macro series (FRED), for the Market desk
# ---------------------------------------------------------------------------
class MacroPoint(Base):
    """One observation of a macro series (e.g. CPI, fed funds), double-dated."""

    __tablename__ = "macro_points"
    __table_args__ = (
        UniqueConstraint("series_id", "ts", name="uq_macro_point"),
        Index("ix_macro_series_ts", "series_id", "ts"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    series_id: Mapped[str] = mapped_column(String(32), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    value: Mapped[float] = mapped_column(Float)
    vendor: Mapped[Optional[str]] = mapped_column(String(32), default=None)
    reference_date: Mapped[Optional[date]] = mapped_column(Date, default=None)
    publication_date: Mapped[Optional[date]] = mapped_column(Date, default=None)
    inserted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ---------------------------------------------------------------------------
# Area: market_data — fundamentals snapshot (for the Fundamentals desk)
# ---------------------------------------------------------------------------
class FundamentalSnapshot(Base):
    """Point-in-time fundamentals/valuation metrics for a ticker."""

    __tablename__ = "fundamental_snapshots"
    __table_args__ = (
        Index("ix_fundamentals_symbol_asof", "symbol", "as_of"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    as_of: Mapped[Optional[date]] = mapped_column(Date, default=None)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    vendor: Mapped[Optional[str]] = mapped_column(String(32), default=None)
    publication_date: Mapped[Optional[date]] = mapped_column(Date, default=None)
    inserted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
