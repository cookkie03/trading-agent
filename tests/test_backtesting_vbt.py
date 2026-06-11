"""Tests for the VectorBT backtest backend (engine='vectorbt') + sweep.

Skipped automatically when the 'backtest' extra (vectorbt) is not installed.
Run with: uv run --extra backtest pytest tests/test_backtesting_vbt.py
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

vbt = pytest.importorskip("vectorbt", reason="requires the 'backtest' extra (vectorbt)")

from tradingagents.backtesting import backtest, sweep  # noqa: E402


def _trend_bars(n, start, step):
    bars = []
    for i in range(n):
        p = start + i * step
        bars.append({"open": p, "high": p + 2, "low": p - 2, "close": p})
    return bars


def test_vbt_uptrend_is_profitable():
    res = backtest(
        _trend_bars(120, 100.0, 1.0),
        engine="vectorbt",
        k_entry=0.0, k_stop=2, k_tp=3, atr_period=14,
    )
    assert res.num_trades > 0
    assert res.total_return > 0


def test_vbt_downtrend_loses_or_flat():
    res = backtest(
        _trend_bars(120, 300.0, -1.0),
        engine="vectorbt",
        k_entry=0.0, k_stop=2, k_tp=3, atr_period=14,
    )
    # In a steady downtrend the long-only strategy should not be profitable.
    assert res.total_return <= 0


def test_vbt_insufficient_data():
    res = backtest(_trend_bars(5, 100.0, 1.0), engine="vectorbt")
    assert res.num_trades == 0
    assert res.total_return == 0.0


def test_vbt_custom_agree_on_direction():
    """Custom and vectorbt engines need not be bit-identical, but they must
    agree on the SIGN of the return on a clear trend (sanity reconciliation)."""
    bars = _trend_bars(150, 100.0, 1.0)
    custom = backtest(bars, engine="custom", k_stop=2, k_tp=3, atr_period=14)
    vbt_res = backtest(bars, engine="vectorbt", k_stop=2, k_tp=3, atr_period=14)
    assert (custom.total_return > 0) == (vbt_res.total_return > 0)


def test_sweep_ranks_by_return():
    bars = _trend_bars(200, 100.0, 1.0)
    grid = sweep(bars, k_stop_grid=[1.0, 2.0, 3.0], k_tp_grid=[2.0, 3.0], atr_period=14)
    assert len(grid) == 6                       # 3 x 2 combos
    # sorted by total_return desc
    returns = [row["total_return"] for row in grid]
    assert returns == sorted(returns, reverse=True)
    # each row carries the params + R:R
    assert all("k_stop" in r and "k_tp" in r and "rr" in r for r in grid)


def test_unknown_engine_raises():
    with pytest.raises(ValueError, match="unknown backtest engine"):
        backtest(_trend_bars(50, 100.0, 1.0), engine="nope")
