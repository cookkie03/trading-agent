from __future__ import annotations

from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Instrument


def upsert_instrument(session: Session, symbol: str, **fields: Any) -> Instrument:
    inst = session.scalar(select(Instrument).where(Instrument.symbol == symbol))
    if inst is None:
        inst = Instrument(symbol=symbol, **fields)
        session.add(inst)
    else:
        for key, value in fields.items():
            setattr(inst, key, value)
    session.flush()
    return inst


def bulk_upsert_instruments(session: Session, rows: Iterable[dict[str, Any]]) -> int:
    """Upsert many instruments (universe sync). Returns the count processed."""
    n = 0
    for row in rows:
        symbol = row["symbol"]
        upsert_instrument(session, symbol, **{k: v for k, v in row.items() if k != "symbol"})
        n += 1
    return n


def list_universe(
    session: Session, *, tradable_only: bool = True, active_only: bool = True
) -> list[Instrument]:
    stmt = select(Instrument)
    if tradable_only:
        stmt = stmt.where(Instrument.tradable.is_(True))
    if active_only:
        stmt = stmt.where(Instrument.active.is_(True))
    return list(session.scalars(stmt))


def universe_symbols(session: Session, **kwargs: Any) -> set[str]:
    return {i.symbol for i in list_universe(session, **kwargs)}


def mark_instruments_inactive(session: Session, symbols: Iterable[str]) -> int:
    """Mark instruments no longer offered by the broker as inactive (reconcile)."""
    symbols = list(symbols)
    if not symbols:
        return 0
    rows = session.scalars(select(Instrument).where(Instrument.symbol.in_(symbols)))
    n = 0
    for inst in rows:
        inst.active = False
        inst.tradable = False
        n += 1
    session.flush()
    return n


def sp500_symbols(session: Session) -> set[str]:
    return set(session.scalars(select(Instrument.symbol).where(Instrument.is_sp500.is_(True))))
