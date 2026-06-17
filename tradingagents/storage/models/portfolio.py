from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import (
    DateTime,
    Float,
    Integer,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Area: rendicontazione (portfolio_state)
# ---------------------------------------------------------------------------
class PortfolioSnapshot(Base):
    """Point-in-time portfolio accounting snapshot (the ``inject_portfolio_state`` source)."""

    __tablename__ = "portfolio_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)
    cash: Mapped[float] = mapped_column(Float, default=0.0)
    total_value: Mapped[float] = mapped_column(Float, default=0.0)
    pnl: Mapped[Optional[float]] = mapped_column(Float, default=None)
    positions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
