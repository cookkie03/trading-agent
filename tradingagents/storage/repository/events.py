from __future__ import annotations

from datetime import date as _date
from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import TickerEvent


def add_ticker_event(
    session: Session, symbol: str, event_date, type: str,
    *, note: Optional[str] = None, source: Optional[str] = None,
) -> TickerEvent:
    """Insert a dated event (idempotent on symbol+date+type)."""
    existing = session.scalar(
        select(TickerEvent).where(
            TickerEvent.symbol == symbol,
            TickerEvent.date == event_date,
            TickerEvent.type == type,
        )
    )
    if existing is not None:
        return existing
    ev = TickerEvent(symbol=symbol, date=event_date, type=type, note=note, source=source)
    session.add(ev)
    session.flush()
    return ev


def due_events(session: Session, *, today=None) -> list[TickerEvent]:
    """Unconsumed events whose date is today or earlier (the system self-wakes)."""
    today = today or _date.today()
    return list(
        session.scalars(
            select(TickerEvent).where(
                TickerEvent.consumed.is_(False),
                TickerEvent.date <= today,
            )
        )
    )


def mark_events_consumed(session: Session, event_ids: Iterable[int]) -> int:
    ids = list(event_ids)
    if not ids:
        return 0
    rows = session.scalars(select(TickerEvent).where(TickerEvent.id.in_(ids)))
    n = 0
    for ev in rows:
        ev.consumed = True
        n += 1
    session.flush()
    return n
