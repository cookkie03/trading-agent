from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import TickerCard


def upsert_ticker_card(session: Session, symbol: str, **fields: Any) -> TickerCard:
    card = session.get(TickerCard, symbol)
    if card is None:
        card = TickerCard(symbol=symbol, **fields)
        session.add(card)
    else:
        for key, value in fields.items():
            setattr(card, key, value)
    session.flush()
    return card


def get_ticker_card(session: Session, symbol: str) -> Optional[TickerCard]:
    return session.get(TickerCard, symbol)


def top_screened(session: Session, limit: int = 10) -> list[TickerCard]:
    """Priority-queue read (D): highest screening_score first."""
    stmt = (
        select(TickerCard)
        .where(TickerCard.screening_score.is_not(None))
        .order_by(TickerCard.screening_score.desc())
        .limit(limit)
    )
    return list(session.scalars(stmt))


def set_watchlist(
    session: Session, symbol: str, in_watchlist: bool, *, reason: Optional[str] = None
) -> TickerCard:
    """Add/remove a ticker from the watchlist, stamping reason + time on entry."""
    fields: dict[str, Any] = {"in_watchlist": in_watchlist}
    if in_watchlist:
        fields["watchlist_reason"] = reason
        fields["watchlist_added_at"] = datetime.now(timezone.utc)
    return upsert_ticker_card(session, symbol, **fields)


def list_watchlist(session: Session) -> list[TickerCard]:
    return list(session.scalars(select(TickerCard).where(TickerCard.in_watchlist.is_(True))))


def watchlist_symbols(session: Session) -> set[str]:
    return set(
        session.scalars(select(TickerCard.symbol).where(TickerCard.in_watchlist.is_(True)))
    )


def watchlist_size(session: Session) -> int:
    return len(watchlist_symbols(session))
