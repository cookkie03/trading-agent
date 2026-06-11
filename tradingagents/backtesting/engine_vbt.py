"""VectorBT backend for the ATR backtest — vectorized engine + parameter sweep.

Same contract as ``engine.py`` (returns ``BacktestResult``) so the two are
interchangeable behind the ``backtest(..., engine=...)`` selector. The custom
engine stays the 1:1-with-live reference; this one trades that fidelity for
*speed at scale*: it can sweep thousands of (k_stop, k_tp, atr_period)
combinations in one vectorized pass — the "continuous threshold validator" the
decision-log (2026-06-04) asks for.

Requires the optional dependency group: ``uv sync --extra backtest``.

Design notes / honest caveats:
- VectorBT applies stops at the *bar* level (vectorized), while the custom
  engine walks intra-bar low/high. Results are close but NOT bit-identical;
  always reconcile on a known case before trusting swept thresholds for live.
- We reuse the project's own ATR (``indicators.core.atr``) computed as a rolling
  series so the levels match what the live system would see, instead of vbt's
  built-in ATR (which uses Wilder smoothing).
"""

from __future__ import annotations

from typing import Any, Optional

from .engine import BacktestResult


def _require_vbt():
    try:
        import vectorbt as vbt  # noqa: F401
        return vbt
    except ImportError as e:  # pragma: no cover - import guard
        raise ImportError(
            "VectorBT backend requires the 'backtest' extra. "
            "Install with: uv sync --extra backtest  (or: uv add --optional backtest vectorbt)"
        ) from e


def _bars_to_frame(bars: list[dict[str, Any]]):
    import pandas as pd

    if not bars:
        return None
    idx = [b.get("ts") for b in bars]
    if any(t is None for t in idx):
        idx = range(len(bars))  # fall back to positional index
    return pd.DataFrame(
        {
            "open": [float(b["open"]) for b in bars],
            "high": [float(b["high"]) for b in bars],
            "low": [float(b["low"]) for b in bars],
            "close": [float(b["close"]) for b in bars],
        },
        index=idx,
    )


def _atr_series(df, period: int):
    """Rolling ATR that matches indicators.core.atr (simple mean of true ranges)."""
    import numpy as np
    import pandas as pd

    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    # core.atr drops the first bar (needs a previous close), so the true-range
    # series effectively starts at index 1; a simple rolling mean matches it.
    return tr.rolling(window=period).mean()


def backtest_vbt(
    bars: list[dict[str, Any]],
    *,
    k_entry: float = 0.0,
    k_stop: float = 2.0,
    k_tp: float = 3.0,
    atr_period: int = 14,
    base_risk_pct: float = 0.01,
    initial_capital: float = 100_000.0,
    fees: float = 0.0,
    direction: str = "longonly",
) -> BacktestResult:
    """Vectorized ATR long backtest. Same signature/return as engine.backtest.

    ``fees`` (fraction, e.g. 0.001 = 10bps) is supported here natively — the
    custom engine ignores costs, so leave it 0.0 for a like-for-like compare.
    """
    vbt = _require_vbt()
    import numpy as np
    import pandas as pd

    from ..domain.enums import Direction
    from ..domain.risk import position_size

    df = _bars_to_frame(bars)
    if df is None or len(df) < atr_period + 2:
        return BacktestResult()

    close = df["close"]
    atr = _atr_series(df, atr_period)

    # Entry levels on the SAME backbone as the live system / custom engine.
    entry_price = close - k_entry * atr
    # Stop/target as fractions of the entry price (vbt wants relative stops).
    with np.errstate(divide="ignore", invalid="ignore"):
        sl_frac = (k_stop * atr) / entry_price
        tp_frac = (k_tp * atr) / entry_price

    # Position sizing: reuse the live risk engine (risk_pct of equity per trade,
    # quantity derived from the ATR stop) so the vbt engine is comparable to the
    # custom one instead of vbt's default "invest all cash". stop_distance is
    # k_stop * ATR; size is in share amount.
    stop_distance = (k_stop * atr).to_numpy()
    px = entry_price.to_numpy()
    size_arr = np.full(len(close), np.nan)
    for i in range(len(close)):
        sd, p = stop_distance[i], px[i]
        if np.isnan(sd) or np.isnan(p) or sd <= 0 or p <= 0:
            continue
        sizing = position_size(initial_capital, p, sd, Direction.BUY, base_risk_pct=base_risk_pct)
        size_arr[i] = sizing.quantity
    size = pd.Series(size_arr, index=close.index)

    # Enter whenever we have a valid ATR/size and are flat; from_signals
    # collapses repeated entries while in a position, mirroring the custom
    # engine's "open only when flat" rule.
    entries = atr.notna() & (atr > 0) & size.notna() & (size > 0)
    entries = entries.fillna(False)

    pf = vbt.Portfolio.from_signals(
        close,
        entries=entries,
        exits=pd.Series(False, index=close.index),
        size=size,
        size_type="amount",
        sl_stop=sl_frac,
        tp_stop=tp_frac,
        init_cash=initial_capital,
        fees=fees,
        direction=direction,
        freq=_infer_freq(close.index),
    )

    return _to_result(pf, initial_capital)


def _infer_freq(index) -> Optional[str]:
    try:
        import pandas as pd

        if isinstance(index, pd.DatetimeIndex):
            return "1D"
    except Exception:
        pass
    return None


def _to_result(pf, initial_capital: float) -> BacktestResult:
    """Map a vbt Portfolio into our BacktestResult contract."""
    trades = pf.trades
    n_tr = int(trades.count())
    if n_tr == 0:
        final_eq = float(pf.value().iloc[-1]) if len(pf.value()) else initial_capital
        return BacktestResult(final_equity=final_eq, total_return=final_eq / initial_capital - 1.0)

    pnl = trades.pnl.values
    wins = int((pnl > 0).sum())
    rec = trades.records_readable
    trade_list: list[dict[str, Any]] = []
    for _, r in rec.iterrows():
        trade_list.append(
            {
                "entry": float(r.get("Avg Entry Price", 0.0)),
                "exit": float(r.get("Avg Exit Price", 0.0)),
                "pnl": float(r.get("PnL", 0.0)),
                "reason": str(r.get("Status", "")),
            }
        )

    final_eq = float(pf.value().iloc[-1])
    return BacktestResult(
        num_trades=n_tr,
        wins=wins,
        hit_rate=(wins / n_tr if n_tr else 0.0),
        total_return=float(pf.total_return()),
        max_drawdown=float(abs(pf.max_drawdown())),
        final_equity=final_eq,
        trades=trade_list,
    )


def sweep(
    bars: list[dict[str, Any]],
    *,
    k_stop_grid: list[float],
    k_tp_grid: list[float],
    atr_period: int = 14,
    base_risk_pct: float = 0.01,
    initial_capital: float = 100_000.0,
    fees: float = 0.0,
) -> list[dict[str, Any]]:
    """Run the ATR backtest over a grid of (k_stop, k_tp) and rank by return.

    This is the reason VectorBT was chosen: validate many threshold combos
    cheaply. Returns a list of dicts sorted by total_return desc, each with the
    params + key metrics. Pure Python loop over the vectorized engine (each run
    is already fast); for very large grids vbt's native broadcasting can be used
    later, but this keeps results trivially mapped to BacktestResult.
    """
    results: list[dict[str, Any]] = []
    for ks in k_stop_grid:
        for kt in k_tp_grid:
            res = backtest_vbt(
                bars,
                k_stop=ks,
                k_tp=kt,
                atr_period=atr_period,
                base_risk_pct=base_risk_pct,
                initial_capital=initial_capital,
                fees=fees,
            )
            results.append(
                {
                    "k_stop": ks,
                    "k_tp": kt,
                    "rr": (kt / ks if ks else 0.0),
                    "num_trades": res.num_trades,
                    "hit_rate": round(res.hit_rate, 4),
                    "total_return": round(res.total_return, 4),
                    "max_drawdown": round(res.max_drawdown, 4),
                }
            )
    results.sort(key=lambda d: d["total_return"], reverse=True)
    return results
