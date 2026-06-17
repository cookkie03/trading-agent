
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import (
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
# Area: logs / trades (execution + audit)
# ---------------------------------------------------------------------------
class Trade(Base):
    """A trade the deterministic Trade function emitted / executed.

    ``client_order_id`` is the idempotency key (anti double-order) used during
    reconciliation; ``broker_order_id`` is the broker's id once confirmed.
    """

    __tablename__ = "trades"
    __table_args__ = (
        UniqueConstraint("client_order_id", name="uq_trade_client_order_id"),
        Index("ix_trades_symbol_ts", "symbol", "ts"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    action: Mapped[str] = mapped_column(String(16))  # buy / sell / hold
    asset_type: Mapped[str] = mapped_column(String(16), default="equity")  # equity / option
    option_type: Mapped[Optional[str]] = mapped_column(String(8), default=None)  # call / put
    quantity: Mapped[Optional[float]] = mapped_column(Float, default=None)
    entry_price: Mapped[Optional[float]] = mapped_column(Float, default=None)
    stop_loss: Mapped[Optional[float]] = mapped_column(Float, default=None)
    take_profit: Mapped[Optional[float]] = mapped_column(Float, default=None)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending/confirmed/cancelled
    commission: Mapped[Optional[float]] = mapped_column(Float, default=None)
    token_cost: Mapped[Optional[float]] = mapped_column(Float, default=None)
    exit_reason: Mapped[Optional[str]] = mapped_column(String(32), default=None)  # tp/sl/trailing/rating
    client_order_id: Mapped[Optional[str]] = mapped_column(String(64), default=None)
    broker_order_id: Mapped[Optional[str]] = mapped_column(String(64), default=None)
    payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ---------------------------------------------------------------------------
# Area: logs — learning-loop substrate (thesis-per-agent <-> outcome)
# ---------------------------------------------------------------------------
class DecisionLog(Base):
    """Every deep-dive decision, logged for the learning loop.

    Captures the per-agent opinions and the final call so that, once trades
    close, outcomes can be matched back to which desk was right (agent scoring /
    weight ponderation). Set up from day one, per the wiki.
    """

    __tablename__ = "decision_log"
    __table_args__ = (
        Index("ix_decisionlog_symbol_ts", "symbol", "ts"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    direction: Mapped[Optional[str]] = mapped_column(String(16), default=None)
    conviction: Mapped[Optional[str]] = mapped_column(String(16), default=None)
    risk_verdict: Mapped[Optional[str]] = mapped_column(String(16), default=None)
    traded: Mapped[bool] = mapped_column(default=False)
    client_order_id: Mapped[Optional[str]] = mapped_column(String(64), default=None)
    agent_opinions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
