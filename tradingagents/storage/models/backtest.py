
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import (
    DateTime,
    Float,
    Integer,
    String,
    Index,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Area: log / backtesting (the nightly threshold validator's output)
# ---------------------------------------------------------------------------
class BacktestResultRow(Base):
    """One nightly backtest/sweep result per symbol.

    The overnight job sweeps the ATR thresholds (k_stop/k_tp/atr_period) per
    watchlist symbol and stores the best combination + its metrics here, plus
    the walk-forward out-of-sample check. Read by the observability dashboard /
    learning loop; it does NOT feed the live cycle directly (thresholds are
    applied via config/charter, deliberately).
    """

    __tablename__ = "backtest_results"
    __table_args__ = (
        Index("ix_backtest_symbol_ts", "symbol", "ts"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    engine: Mapped[str] = mapped_column(String(16), default="vectorbt")
    rank_by: Mapped[str] = mapped_column(String(16), default="sharpe")
    # best params found in-sample
    k_stop: Mapped[Optional[float]] = mapped_column(default=None)
    k_tp: Mapped[Optional[float]] = mapped_column(default=None)
    atr_period: Mapped[Optional[int]] = mapped_column(default=None)
    # headline metrics of the best combo
    num_trades: Mapped[int] = mapped_column(Integer, default=0)
    hit_rate: Mapped[float] = mapped_column(default=0.0)
    total_return: Mapped[float] = mapped_column(default=0.0)
    max_drawdown: Mapped[float] = mapped_column(default=0.0)
    sharpe: Mapped[float] = mapped_column(default=0.0)
    sortino: Mapped[float] = mapped_column(default=0.0)
    calmar: Mapped[float] = mapped_column(default=0.0)
    # walk-forward out-of-sample summary
    oos_mean_sharpe: Mapped[Optional[float]] = mapped_column(default=None)
    oos_mean_return: Mapped[Optional[float]] = mapped_column(default=None)
    robust_params: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)  # full sweep top-N + folds
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
