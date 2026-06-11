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


def test_sweep_ranks_by_metric():
    bars = _trend_bars(200, 100.0, 1.0)
    grid = sweep(bars, k_stop_grid=[1.0, 2.0, 3.0], k_tp_grid=[2.0, 3.0], atr_period=14)
    # R:R < 1 combos are skipped (k_stop=3, k_tp=2 -> 0.67). Expected kept: 5.
    assert len(grid) == 5
    # default ranking is by sharpe, descending
    sharpes = [row["sharpe"] for row in grid]
    assert sharpes == sorted(sharpes, reverse=True)
    # each row carries params (incl. atr_period) + extended metrics
    assert all({"k_stop", "k_tp", "atr_period", "rr", "sharpe", "sortino", "calmar"} <= r.keys() for r in grid)


def test_sweep_3d_grid_with_atr_periods():
    bars = _trend_bars(250, 100.0, 1.0)
    grid = sweep(
        bars,
        k_stop_grid=[1.0, 2.0], k_tp_grid=[2.0, 3.0],
        atr_period_grid=[10, 14], rank_by="total_return",
    )
    # 2 k_stop × 2 k_tp × 2 atr = 8 combos, all R:R >= 1
    assert len(grid) == 8
    rets = [r["total_return"] for r in grid]
    assert rets == sorted(rets, reverse=True)
    assert {r["atr_period"] for r in grid} == {10, 14}


def test_sweep_invalid_rank_by_raises():
    with pytest.raises(ValueError, match="rank_by must be one of"):
        sweep(_trend_bars(60, 100.0, 1.0), k_stop_grid=[2.0], k_tp_grid=[3.0], rank_by="nope")


def test_walk_forward_returns_oos_and_robust():
    from tradingagents.backtesting import walk_forward

    bars = _trend_bars(300, 100.0, 1.0)
    wf = walk_forward(
        bars, k_stop_grid=[1.0, 2.0, 3.0], k_tp_grid=[2.0, 3.0],
        atr_period_grid=[14], n_splits=3,
    )
    assert "folds" in wf and "oos_mean_sharpe" in wf
    assert wf["robust_params"] is not None
    assert {"k_stop", "k_tp", "atr_period"} <= wf["robust_params"].keys()


def test_walk_forward_short_history_is_safe():
    from tradingagents.backtesting import walk_forward

    wf = walk_forward(_trend_bars(40, 100.0, 1.0), k_stop_grid=[2.0], k_tp_grid=[3.0])
    assert wf["folds"] == []
    assert wf["robust_params"] is None


def test_unknown_engine_raises():
    with pytest.raises(ValueError, match="unknown backtest engine"):
        backtest(_trend_bars(50, 100.0, 1.0), engine="nope")
