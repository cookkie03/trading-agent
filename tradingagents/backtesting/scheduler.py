"""Nightly threshold-validator job.

Per the decision-log (2026-06-04): backtesting is a *continuous, asynchronous*
validator of the thresholds the live system is tuned on (k_stop/k_tp/ATR period,
sizing) — NOT a tool the agents call, and NOT run inside the trading cycle. This
module is that job: it runs while the market is closed (overnight), sweeps the
ATR thresholds per watchlist symbol with the VectorBT engine, validates them
walk-forward (out-of-sample, anti-overfitting), persists the results, and —
optionally — writes the robust params back into the charter.

Wiring:
- ``run_nightly_backtest(...)`` does one full pass and returns a summary.
- ``seconds_until_hour(hour)`` computes the sleep until the next HH:00 local.
- ``nightly_loop(...)`` sleeps to the configured hour, runs, repeats (used by the
  daemon when ``[backtest] nightly_enabled`` is true).
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

from ..storage import database, repository as repo
from ..indicators.db import recent_bars


def seconds_until_hour(hour: int, *, now: Optional[datetime] = None) -> float:
    """Seconds from ``now`` until the next occurrence of local HH:00."""
    now = now or datetime.now()
    target = now.replace(hour=hour % 24, minute=0, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


def _symbols(session) -> list[str]:
    """Watchlist first (what we actually trade); fall back to the universe."""
    syms = sorted(repo.watchlist_symbols(session))
    if syms:
        return syms
    return sorted(repo.universe_symbols(session))


def run_nightly_backtest(
    *,
    settings: Any,
    db_url: Optional[str] = None,
    symbols: Optional[list[str]] = None,
    log: Callable[[str], None] = print,
) -> dict[str, Any]:
    """One full overnight pass: sweep + walk-forward per symbol, persist results.

    Returns a summary dict: {ran, symbols, persisted, applied, top: [...]}.
    Uses the VectorBT engine (sweep/walk_forward); if the 'backtest' extra is
    missing it logs and returns ran=0 instead of crashing the daemon.
    """
    from ..storage.models import BacktestResultRow

    try:
        from .engine_vbt import sweep, walk_forward
    except ImportError as e:
        log(f"[backtest] VectorBT not available ({e}); skipping nightly job.")
        return {"ran": 0, "reason": "vectorbt-missing"}

    bt = settings.backtest
    database.init_db(db_url)

    with database.get_session() as s:
        syms = symbols or _symbols(s)

    if not syms:
        log("[backtest] no symbols in watchlist/universe; nothing to validate.")
        return {"ran": 0, "reason": "no-symbols"}

    log(f"[backtest] nightly sweep over {len(syms)} symbols "
        f"(grid {len(bt.k_stop_grid)}×{len(bt.k_tp_grid)}×{len(bt.atr_period_grid)}, rank={bt.rank_by})")

    persisted = 0
    applied = 0
    top: list[dict[str, Any]] = []

    for sym in syms:
        with database.get_session() as s:
            bars = recent_bars(s, sym, interval="1d", lookback=bt.lookback)
        if len(bars) < max(bt.atr_period_grid) + 30:
            log(f"[backtest] {sym}: only {len(bars)} bars, skipping (need history).")
            continue

        ranked = sweep(
            bars,
            k_stop_grid=bt.k_stop_grid, k_tp_grid=bt.k_tp_grid,
            atr_period_grid=bt.atr_period_grid,
            base_risk_pct=bt.base_risk_pct, initial_capital=bt.initial_capital,
            fees=bt.fees, rank_by=bt.rank_by,
        )
        if not ranked:
            continue
        best = ranked[0]

        wf = walk_forward(
            bars,
            k_stop_grid=bt.k_stop_grid, k_tp_grid=bt.k_tp_grid,
            atr_period_grid=bt.atr_period_grid, n_splits=bt.wf_splits,
            base_risk_pct=bt.base_risk_pct, initial_capital=bt.initial_capital,
            fees=bt.fees, rank_by=bt.rank_by,
        )

        with database.get_session() as s:
            s.add(BacktestResultRow(
                symbol=sym, engine="vectorbt", rank_by=bt.rank_by,
                k_stop=best["k_stop"], k_tp=best["k_tp"], atr_period=best["atr_period"],
                num_trades=best["num_trades"], hit_rate=best["hit_rate"],
                total_return=best["total_return"], max_drawdown=best["max_drawdown"],
                sharpe=best["sharpe"], sortino=best["sortino"], calmar=best["calmar"],
                oos_mean_sharpe=wf.get("oos_mean_sharpe"),
                oos_mean_return=wf.get("oos_mean_return"),
                robust_params=wf.get("robust_params") or {},
                payload={"top": ranked[:5], "folds": wf.get("folds", [])},
            ))
        persisted += 1
        top.append({"symbol": sym, **{k: best[k] for k in
                    ("k_stop", "k_tp", "atr_period", "sharpe", "total_return", "num_trades")},
                    "oos_sharpe": wf.get("oos_mean_sharpe")})
        log(f"[backtest] {sym}: best k_stop={best['k_stop']} k_tp={best['k_tp']} "
            f"atr={best['atr_period']} sharpe={best['sharpe']} "
            f"oos_sharpe={wf.get('oos_mean_sharpe')}")

    # Optionally fold the cross-symbol robust params back into the charter.
    if bt.apply_robust and top:
        applied = _apply_robust_params(top, db_url=db_url, log=log)

    log(f"[backtest] nightly done: {persisted}/{len(syms)} symbols persisted, applied={applied}")
    return {"ran": 1, "symbols": len(syms), "persisted": persisted, "applied": applied, "top": top}


def _apply_robust_params(top: list[dict[str, Any]], *, db_url: Optional[str], log: Callable[[str], None]) -> int:
    """Write the median best k_stop/k_tp/atr_period across symbols into the charter.

    Conservative: uses the median (not the single best) so one lucky symbol
    cannot move the live thresholds. Only the deterministic, backtest-tunable
    knobs are touched.
    """
    import statistics as st

    ks = st.median(t["k_stop"] for t in top)
    kt = st.median(t["k_tp"] for t in top)
    ap = int(st.median(t["atr_period"] for t in top))
    with database.get_session() as s:
        repo.set_charter_rule(s, "k_stop", ks, "backtest-tuned (nightly walk-forward)")
        repo.set_charter_rule(s, "k_tp", kt, "backtest-tuned (nightly walk-forward)")
        repo.set_charter_rule(s, "atr_period", ap, "backtest-tuned (nightly walk-forward)")
    log(f"[backtest] applied robust params to charter: k_stop={ks} k_tp={kt} atr_period={ap}")
    return 3


def nightly_loop(
    *,
    settings: Any,
    db_url: Optional[str] = None,
    sleep: Callable[[float], None] = time.sleep,
    max_runs: Optional[int] = None,
    log: Callable[[str], None] = print,
) -> None:
    """Sleep until the configured nightly hour, run the job, repeat.

    ``max_runs`` + injectable ``sleep`` make it testable; with the defaults it
    runs forever. Exceptions in a single run are logged and never kill the loop.
    """
    bt = settings.backtest
    runs = 0
    while max_runs is None or runs < max_runs:
        wait = seconds_until_hour(bt.nightly_hour)
        log(f"[backtest] next nightly run in {wait/3600:.1f}h (at {bt.nightly_hour:02d}:00 local)")
        sleep(wait)
        try:
            run_nightly_backtest(settings=settings, db_url=db_url, log=log)
        except Exception as e:  # never let the scheduler die
            log(f"[backtest] nightly run failed: {type(e).__name__}: {e}")
        runs += 1
