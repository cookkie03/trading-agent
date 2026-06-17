from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import PortfolioSnapshot


def save_portfolio_snapshot(
    session: Session,
    *,
    cash: float,
    total_value: float,
    positions: Optional[list[dict[str, Any]]] = None,
    pnl: Optional[float] = None,
) -> PortfolioSnapshot:
    snap = PortfolioSnapshot(
        cash=cash,
        total_value=total_value,
        positions=positions or [],
        pnl=pnl,
    )
    session.add(snap)
    session.flush()
    return snap


def latest_portfolio_snapshot(session: Session) -> Optional[PortfolioSnapshot]:
    stmt = select(PortfolioSnapshot).order_by(PortfolioSnapshot.ts.desc()).limit(1)
    return session.scalar(stmt)


def first_portfolio_snapshot_on_or_after(
    session: Session, ts=None
) -> Optional[PortfolioSnapshot]:
    """Earliest snapshot (optionally at/after ``ts``) — the baseline for returns."""
    stmt = select(PortfolioSnapshot)
    if ts is not None:
        stmt = stmt.where(PortfolioSnapshot.ts >= ts)
    return session.scalar(stmt.order_by(PortfolioSnapshot.ts.asc()).limit(1))
