from __future__ import annotations

from typing import Any, Iterable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    FundamentalSnapshot,
    MacroPoint,
    NewsItem,
    PriceBar,
    SocialPost,
)


def insert_price_bars(session: Session, symbol: str, bars: Iterable[dict[str, Any]]) -> int:
    """Bulk-insert OHLCV bars. Returns the number of rows added."""
    rows = [PriceBar(symbol=symbol, **bar) for bar in bars]
    session.add_all(rows)
    session.flush()
    return len(rows)


def existing_news_keys(session: Session, symbol: str) -> set[str]:
    """Dedup keys already stored for a symbol (DB-first news ingestion)."""
    return set(
        session.scalars(select(NewsItem.dedup_key).where(NewsItem.symbol == symbol))
    )


def insert_news_items(session: Session, symbol: str, items: Iterable[dict[str, Any]]) -> int:
    rows = [NewsItem(symbol=symbol, **item) for item in items]
    session.add_all(rows)
    session.flush()
    return len(rows)


def recent_news(session: Session, symbol: str, *, limit: int = 10) -> list[NewsItem]:
    stmt = (
        select(NewsItem)
        .where(NewsItem.symbol == symbol)
        .order_by(NewsItem.ts.desc())
        .limit(limit)
    )
    return list(session.scalars(stmt))


def existing_macro_ts(session: Session, series_id: str) -> set:
    return set(session.scalars(select(MacroPoint.ts).where(MacroPoint.series_id == series_id)))


def insert_macro_points(session: Session, series_id: str, points: Iterable[dict[str, Any]]) -> int:
    rows = [MacroPoint(series_id=series_id, **p) for p in points]
    session.add_all(rows)
    session.flush()
    return len(rows)


def latest_macro(session: Session, series_id: str) -> Optional[MacroPoint]:
    stmt = (
        select(MacroPoint)
        .where(MacroPoint.series_id == series_id)
        .order_by(MacroPoint.ts.desc())
        .limit(1)
    )
    return session.scalar(stmt)


def save_fundamentals(
    session: Session, symbol: str, metrics: dict[str, Any], *, as_of=None, vendor=None
) -> FundamentalSnapshot:
    snap = FundamentalSnapshot(symbol=symbol, metrics=metrics, as_of=as_of, vendor=vendor)
    session.add(snap)
    session.flush()
    return snap


def latest_fundamentals(session: Session, symbol: str) -> Optional[FundamentalSnapshot]:
    stmt = (
        select(FundamentalSnapshot)
        .where(FundamentalSnapshot.symbol == symbol)
        .order_by(FundamentalSnapshot.inserted_at.desc(), FundamentalSnapshot.id.desc())
        .limit(1)
    )
    return session.scalar(stmt)


def existing_social_keys(session: Session, symbol: str) -> set[str]:
    return set(session.scalars(select(SocialPost.dedup_key).where(SocialPost.symbol == symbol)))


def insert_social_posts(session: Session, symbol: str, items: Iterable[dict[str, Any]]) -> int:
    rows = [SocialPost(symbol=symbol, **it) for it in items]
    session.add_all(rows)
    session.flush()
    return len(rows)


def recent_social(session: Session, symbol: str, *, limit: int = 15) -> list[SocialPost]:
    stmt = (
        select(SocialPost)
        .where(SocialPost.symbol == symbol)
        .order_by(SocialPost.ts.desc())
        .limit(limit)
    )
    return list(session.scalars(stmt))


def latest_price(session: Session, symbol: str, interval: str = "1d") -> Optional[PriceBar]:
    stmt = (
        select(PriceBar)
        .where(PriceBar.symbol == symbol, PriceBar.interval == interval)
        .order_by(PriceBar.ts.desc())
        .limit(1)
    )
    return session.scalar(stmt)


def first_price_on_or_after(
    session: Session, symbol: str, ts, interval: str = "1d"
) -> Optional[PriceBar]:
    """Earliest stored bar at/after ``ts`` (for return-since calculations)."""
    stmt = (
        select(PriceBar)
        .where(PriceBar.symbol == symbol, PriceBar.interval == interval, PriceBar.ts >= ts)
        .order_by(PriceBar.ts.asc())
        .limit(1)
    )
    return session.scalar(stmt)
