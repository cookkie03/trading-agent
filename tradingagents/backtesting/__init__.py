"""Deterministic backtester (the continuous threshold validator).

Per the wiki, backtesting is a deterministic Python process over the internal
historical DB — *no LLM in the loop* — used to validate the thresholds the rest
of the system is tuned on (R:R, k_stop/k_tp, ATR period, sizing). It reuses our
own indicators + risk engine, so what it validates is exactly what runs live.

Two interchangeable engines behind the same ``BacktestResult`` contract:

- ``engine="custom"`` (default): the hand-rolled event-driven engine in
  ``engine.py``. Walks bars intra-bar (low/high) — the 1:1-with-live reference.
- ``engine="vectorbt"``: the vectorized engine in ``engine_vbt.py`` (requires
  the ``backtest`` extra: ``uv sync --extra backtest``). Much faster at scale —
  use it for parameter sweeps via ``sweep()``. Applies stops at bar level, so
  reconcile against the custom engine on a known case before trusting numbers.
"""

from __future__ import annotations

from typing import Any

from .engine import BacktestResult, backtest as _backtest_custom, run_backtest


def backtest(bars: list[dict[str, Any]], *, engine: str = "custom", **params: Any) -> BacktestResult:
    """Run the ATR backtest with the selected engine ('custom' | 'vectorbt')."""
    if engine == "custom":
        return _backtest_custom(bars, **params)
    if engine in ("vectorbt", "vbt"):
        from .engine_vbt import backtest_vbt
        return backtest_vbt(bars, **params)
    raise ValueError(f"unknown backtest engine '{engine}' (known: custom, vectorbt)")


def sweep(bars: list[dict[str, Any]], **kwargs: Any) -> list[dict[str, Any]]:
    """Parameter sweep over a (k_stop, k_tp) grid using the VectorBT engine.

    Requires the 'backtest' extra. See engine_vbt.sweep for the signature.
    """
    from .engine_vbt import sweep as _sweep
    return _sweep(bars, **kwargs)


__all__ = ["BacktestResult", "backtest", "run_backtest", "sweep"]
