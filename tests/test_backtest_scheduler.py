"""Tests for the nightly backtest scheduler (timing + end-to-end persistence)."""

from __future__ import annotations

from datetime import datetime

import pytest

pytestmark = pytest.mark.unit

vbt = pytest.importorskip("vectorbt", reason="requires the 'backtest' extra (vectorbt)")

from tradingagents.backtesting.scheduler import (  # noqa: E402
    seconds_until_hour,
    run_nightly_backtest,
    nightly_loop,
)
from tradingagents.config import load_settings  # noqa: E402
from tradingagents.storage import database, repository as repo  # noqa: E402
from tradingagents.storage.models import BacktestResultRow, PriceBar  # noqa: E402


def test_seconds_until_hour_future_same_day():
    now = datetime(2026, 6, 10, 1, 0, 0)        # 01:00, target 02:00 -> 1h
    assert seconds_until_hour(2, now=now) == 3600.0


def test_seconds_until_hour_wraps_to_next_day():
    now = datetime(2026, 6, 10, 3, 0, 0)        # 03:00, target 02:00 -> 23h
    assert seconds_until_hour(2, now=now) == 23 * 3600.0


def _seed_bars(session, symbol, n=300, start=100.0, step=1.0):
    from datetime import timedelta, timezone
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    for i in range(n):
        p = start + i * step
        session.add(PriceBar(
            symbol=symbol, ts=base + timedelta(days=i), interval="1d",
            open=p, high=p + 2, low=p - 2, close=p, volume=1000.0,
        ))


def test_run_nightly_backtest_persists(tmp_path):
    db_url = f"sqlite:///{tmp_path/'bt.db'}"
    database.init_db(db_url)
    with database.get_session() as s:
        repo.set_watchlist(s, "AAPL", True, reason="test")
        _seed_bars(s, "AAPL", n=300)

    settings = load_settings(None)
    settings.backtest.k_stop_grid = [1.0, 2.0]
    settings.backtest.k_tp_grid = [2.0, 3.0]
    settings.backtest.atr_period_grid = [14]
    settings.backtest.wf_splits = 3
    settings.backtest.apply_robust = False

    out = run_nightly_backtest(settings=settings, db_url=db_url, log=lambda *_: None)
    assert out["ran"] == 1
    assert out["persisted"] == 1

    with database.get_session() as s:
        rows = list(s.query(BacktestResultRow).all())
    assert len(rows) == 1
    assert rows[0].symbol == "AAPL"
    assert rows[0].k_stop in (1.0, 2.0)
    assert rows[0].engine == "vectorbt"


def test_run_nightly_no_symbols(tmp_path):
    db_url = f"sqlite:///{tmp_path/'empty.db'}"
    settings = load_settings(None)
    out = run_nightly_backtest(settings=settings, db_url=db_url, log=lambda *_: None)
    assert out["ran"] == 0


def test_apply_robust_writes_charter(tmp_path):
    db_url = f"sqlite:///{tmp_path/'bt2.db'}"
    database.init_db(db_url)
    with database.get_session() as s:
        repo.set_watchlist(s, "AAPL", True, reason="test")
        _seed_bars(s, "AAPL", n=300)

    settings = load_settings(None)
    settings.backtest.k_stop_grid = [1.0, 2.0]
    settings.backtest.k_tp_grid = [2.0, 3.0]
    settings.backtest.atr_period_grid = [14]
    settings.backtest.apply_robust = True

    out = run_nightly_backtest(settings=settings, db_url=db_url, log=lambda *_: None)
    assert out["applied"] == 3
    with database.get_session() as s:
        charter = repo.load_charter(s)
    assert "k_stop" in charter and "k_tp" in charter and "atr_period" in charter


def test_nightly_loop_runs_once_then_stops(tmp_path, monkeypatch):
    db_url = f"sqlite:///{tmp_path/'loop.db'}"
    database.init_db(db_url)
    with database.get_session() as s:
        repo.set_watchlist(s, "AAPL", True, reason="test")
        _seed_bars(s, "AAPL", n=300)

    settings = load_settings(None)
    settings.backtest.k_stop_grid = [2.0]
    settings.backtest.k_tp_grid = [3.0]
    settings.backtest.atr_period_grid = [14]

    calls = {"sleep": 0}

    def fake_sleep(_):
        calls["sleep"] += 1

    nightly_loop(settings=settings, db_url=db_url, sleep=fake_sleep, max_runs=1, log=lambda *_: None)
    assert calls["sleep"] == 1   # slept once before the single run
