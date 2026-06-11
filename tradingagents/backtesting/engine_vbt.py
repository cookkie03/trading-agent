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


def _safe(fn, default: float = 0.0) -> float:
    """Call a vbt metric, coercing NaN/inf/errors to a finite default."""
    import math

    try:
        v = float(fn())
        return v if math.isfinite(v) else default
    except Exception:
        return default


def _to_result(pf, initial_capital: float) -> BacktestResult:
    """Map a vbt Portfolio into our BacktestResult contract (with extended metrics)."""
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

    # Profit factor = gross profit / gross loss
    gross_profit = float(pnl[pnl > 0].sum())
    gross_loss = float(-pnl[pnl < 0].sum())
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0.0

    final_eq = float(pf.value().iloc[-1])
    return BacktestResult(
        num_trades=n_tr,
        wins=wins,
        hit_rate=(wins / n_tr if n_tr else 0.0),
        total_return=_safe(pf.total_return),
        max_drawdown=abs(_safe(pf.max_drawdown)),
        final_equity=final_eq,
        sharpe=_safe(pf.sharpe_ratio),
        sortino=_safe(pf.sortino_ratio),
        calmar=_safe(pf.calmar_ratio),
        profit_factor=round(profit_factor, 4),
        trades=trade_list,
    )


def sweep(
    bars: list[dict[str, Any]],
    *,
    k_stop_grid: list[float],
    k_tp_grid: list[float],
    atr_period_grid: Optional[list[int]] = None,
    atr_period: int = 14,
    base_risk_pct: float = 0.01,
    initial_capital: float = 100_000.0,
    fees: float = 0.0,
    rank_by: str = "sharpe",
) -> list[dict[str, Any]]:
    """Grid-search the ATR strategy over (k_stop, k_tp, atr_period) and rank.

    This is the reason VectorBT was chosen: validate many threshold combos
    cheaply. Returns a list of dicts sorted by ``rank_by`` desc (default
    'sharpe' — more robust than raw return), each with params + key metrics.

    ``atr_period_grid`` (optional) sweeps the ATR window too; if omitted, only
    the single ``atr_period`` is used. Only combos with R:R = k_tp/k_stop >= 1
    are kept (a target tighter than the stop is never worth testing).
    """
    periods = atr_period_grid or [atr_period]
    valid_metrics = {"sharpe", "sortino", "calmar", "total_return", "profit_factor"}
    if rank_by not in valid_metrics:
        raise ValueError(f"rank_by must be one of {sorted(valid_metrics)}")

    results: list[dict[str, Any]] = []
    for ap in periods:
        for ks in k_stop_grid:
            for kt in k_tp_grid:
                if ks <= 0 or kt / ks < 1.0:   # skip R:R < 1
                    continue
                res = backtest_vbt(
                    bars,
                    k_stop=ks,
                    k_tp=kt,
                    atr_period=ap,
                    base_risk_pct=base_risk_pct,
                    initial_capital=initial_capital,
                    fees=fees,
                )
                results.append(
                    {
                        "k_stop": ks,
                        "k_tp": kt,
                        "atr_period": ap,
                        "rr": round(kt / ks, 3),
                        "num_trades": res.num_trades,
                        "hit_rate": round(res.hit_rate, 4),
                        "total_return": round(res.total_return, 4),
                        "max_drawdown": round(res.max_drawdown, 4),
                        "sharpe": round(res.sharpe, 4),
                        "sortino": round(res.sortino, 4),
                        "calmar": round(res.calmar, 4),
                        "profit_factor": res.profit_factor,
                    }
                )
    results.sort(key=lambda d: d[rank_by], reverse=True)
    return results


def walk_forward(
    bars: list[dict[str, Any]],
    *,
    k_stop_grid: list[float],
    k_tp_grid: list[float],
    atr_period_grid: Optional[list[int]] = None,
    n_splits: int = 4,
    train_frac: float = 0.6,
    base_risk_pct: float = 0.01,
    initial_capital: float = 100_000.0,
    fees: float = 0.0,
    rank_by: str = "sharpe",
) -> dict[str, Any]:
    """Walk-forward validation: tune on in-sample, measure on out-of-sample.

    Splits the bar history into ``n_splits`` contiguous windows; for each, the
    best params are picked on the first ``train_frac`` (in-sample) and then
    *applied* to the remaining out-of-sample slice. Robust params are those that
    keep working out-of-sample — the anti-overfitting guard the strategy needs
    (decision-log: walk-forward / out-of-sample, questions-for-salvatore).

    Returns {'folds': [...], 'oos_mean_sharpe': x, 'oos_mean_return': y,
             'robust_params': {...}} where robust_params is the most frequent
    best-param combo across folds.
    """
    from collections import Counter

    n = len(bars)
    if n < 80:
        return {"folds": [], "oos_mean_sharpe": 0.0, "oos_mean_return": 0.0, "robust_params": None}

    fold_size = n // n_splits
    folds: list[dict[str, Any]] = []
    best_keys: list[tuple] = []

    for i in range(n_splits):
        lo = i * fold_size
        hi = n if i == n_splits - 1 else (i + 1) * fold_size
        window = bars[lo:hi]
        if len(window) < 40:
            continue
        cut = int(len(window) * train_frac)
        train, test = window[:cut], window[cut:]
        if len(train) < 20 or len(test) < 20:
            continue

        ranked = sweep(
            train,
            k_stop_grid=k_stop_grid, k_tp_grid=k_tp_grid,
            atr_period_grid=atr_period_grid,
            base_risk_pct=base_risk_pct, initial_capital=initial_capital,
            fees=fees, rank_by=rank_by,
        )
        if not ranked:
            continue
        best = ranked[0]
        # apply best params out-of-sample
        oos = backtest_vbt(
            test,
            k_stop=best["k_stop"], k_tp=best["k_tp"], atr_period=best["atr_period"],
            base_risk_pct=base_risk_pct, initial_capital=initial_capital, fees=fees,
        )
        folds.append({
            "fold": i,
            "best_params": {"k_stop": best["k_stop"], "k_tp": best["k_tp"], "atr_period": best["atr_period"]},
            "in_sample_sharpe": best["sharpe"],
            "oos_sharpe": round(oos.sharpe, 4),
            "oos_return": round(oos.total_return, 4),
            "oos_trades": oos.num_trades,
        })
        best_keys.append((best["k_stop"], best["k_tp"], best["atr_period"]))

    if not folds:
        return {"folds": [], "oos_mean_sharpe": 0.0, "oos_mean_return": 0.0, "robust_params": None}

    oos_mean_sharpe = round(sum(f["oos_sharpe"] for f in folds) / len(folds), 4)
    oos_mean_return = round(sum(f["oos_return"] for f in folds) / len(folds), 4)
    common = Counter(best_keys).most_common(1)[0][0]
    robust = {"k_stop": common[0], "k_tp": common[1], "atr_period": common[2]}
    return {
        "folds": folds,
        "oos_mean_sharpe": oos_mean_sharpe,
        "oos_mean_return": oos_mean_return,
        "robust_params": robust,
    }
