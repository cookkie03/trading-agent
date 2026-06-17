from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Instrument, Trade

from .portfolio import latest_portfolio_snapshot


def record_trade(session: Session, symbol: str, action: str, **fields: Any) -> Trade:
    trade = Trade(symbol=symbol, action=action, **fields)
    session.add(trade)
    session.flush()
    return trade


def trade_by_client_order_id(session: Session, client_order_id: str) -> Optional[Trade]:
    """Idempotency lookup used during broker reconciliation."""
    return session.scalar(
        select(Trade).where(Trade.client_order_id == client_order_id)
    )


def open_trades(session: Session) -> list[Trade]:
    """Filled long positions not yet closed (candidates for exit management)."""
    return list(
        session.scalars(
            select(Trade).where(Trade.status == "filled", Trade.action == "buy")
        )
    )


def instrument_sector(session: Session, symbol: str) -> Optional[str]:
    inst = session.scalar(select(Instrument).where(Instrument.symbol == symbol))
    return inst.sector if inst is not None else None


def sector_exposure(session: Session) -> dict[str, float]:
    """Current portfolio exposure per sector, as a fraction of total value."""
    snap = latest_portfolio_snapshot(session)
    total = float(snap.total_value) if snap is not None else 0.0
    exposure: dict[str, float] = {}
    for t in open_trades(session):
        sector = instrument_sector(session, t.symbol)
        if not sector or t.entry_price is None or not t.quantity:
            continue
        exposure[sector] = exposure.get(sector, 0.0) + t.entry_price * t.quantity
    if total > 0:
        exposure = {k: v / total for k, v in exposure.items()}
    return exposure
