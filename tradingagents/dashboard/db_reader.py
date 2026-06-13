"""
DB Reader — legge i dati dal DB SQLite del trading-agent.

Usa le stesse definizioni dei modelli SQLAlchemy del progetto
per garantire compatibilità. Il path al DB è risolto nello stesso
modo di tradingagents.storage.database (default: ~/.tradingagents/trading_agent.db).
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import pandas as pd
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker

_DEFAULT_DB = Path(os.path.expanduser("~")) / ".tradingagents" / "trading_agent.db"
_DB_URL = os.environ.get("TRADINGAGENTS_DATABASE_URL", f"sqlite:///{_DEFAULT_DB}")

_engine = None
_session_factory = None


def _get_engine():
    global _engine
    if _engine is None:
        import os as _os
        _db_path = str(_DEFAULT_DB)
        _url = _os.environ.get("TRADINGAGENTS_DATABASE_URL", f"sqlite:///{_db_path}")
        _engine = create_engine(
            _url,
            echo=False,
            connect_args={"timeout": 30},
            pool_pre_ping=True,
        )
        # Enable WAL mode for concurrent reads
        try:
            with _engine.connect() as _c:
                _c.execute(text("PRAGMA journal_mode=WAL"))
        except Exception:
            pass
    return _engine


def _get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=_get_engine())
    return _session_factory


@contextmanager
def get_session() -> Iterator[Session]:
    sess = _get_session_factory()()
    try:
        yield sess
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    finally:
        sess.close()


def query_df(sql: str, params: dict | None = None) -> pd.DataFrame:
    """Esegue una query SQL e restituisce un DataFrame."""
    with _get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


def table_exists(table_name: str) -> bool:
    """Controlla se una tabella esiste nel DB."""
    if not _DEFAULT_DB.exists():
        return False
    with _get_engine().connect() as conn:
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name=:t"),
            {"t": table_name},
        )
        return result.fetchone() is not None


# ══════════════════════════════════════════════════════════════════════════════
# Portfolio & Positions
# ══════════════════════════════════════════════════════════════════════════════

def get_portfolio_history(limit: int = 500) -> pd.DataFrame:
    """Storico NAV / portfolio snapshot, ordinato per data desc."""
    if not table_exists("portfolio_snapshots"):
        return pd.DataFrame()
    return query_df(
        "SELECT * FROM portfolio_snapshots ORDER BY ts DESC LIMIT :limit",
        {"limit": limit},
    )


def get_latest_portfolio() -> dict | None:
    """Ultimo portfolio snapshot come dict."""
    df = query_df("SELECT * FROM portfolio_snapshots ORDER BY ts DESC LIMIT 1")
    if df.empty:
        return None
    return df.iloc[0].to_dict()


def get_trades_df(limit: int = 200) -> pd.DataFrame:
    """Tutti i trade, ordinati per data desc."""
    if not table_exists("trades"):
        return pd.DataFrame()
    return query_df(
        "SELECT * FROM trades ORDER BY ts DESC LIMIT :limit",
        {"limit": limit},
    )


def get_trades_by_status(status: str, limit: int = 200) -> pd.DataFrame:
    if not table_exists("trades"):
        return pd.DataFrame()
    return query_df(
        "SELECT * FROM trades WHERE status=:s ORDER BY ts DESC LIMIT :limit",
        {"s": status, "limit": limit},
    )


def get_open_trades() -> pd.DataFrame:
    return get_trades_by_status("filled")


# ══════════════════════════════════════════════════════════════════════════════
# Research States & Ticker Cards
# ══════════════════════════════════════════════════════════════════════════════

def get_recent_research_states(limit: int = 50) -> pd.DataFrame:
    """Stati di ricerca piC recenti (tesi sealed)."""
    if not table_exists("research_states"):
        return pd.DataFrame()
    return query_df(
        "SELECT * FROM research_states ORDER BY created_at DESC LIMIT :limit",
        {"limit": limit},
    )


def get_watchlist_df() -> pd.DataFrame:
    """Watchlist corrente con screening score e latest direction."""
    if not table_exists("ticker_card"):
        return pd.DataFrame()
    return query_df(
        "SELECT symbol, screening_score, latest_direction, latest_conviction, "
        "next_check_date, in_portfolio, watchlist_reason "
        "FROM ticker_card WHERE in_watchlist=1 "
        "ORDER BY screening_score DESC"
    )


def get_ticker_card(symbol: str) -> dict | None:
    """Singola ticker card."""
    if not table_exists("ticker_card"):
        return None
    df = query_df(
        "SELECT * FROM ticker_card WHERE symbol=:s", {"s": symbol}
    )
    return df.iloc[0].to_dict() if not df.empty else None


def get_universe_size() -> int:
    if not table_exists("instruments"):
        return 0
    df = query_df("SELECT COUNT(*) as n FROM instruments WHERE tradable=1")
    return int(df.iloc[0]["n"]) if not df.empty else 0


def get_watchlist_size() -> int:
    if not table_exists("ticker_card"):
        return 0
    df = query_df("SELECT COUNT(*) as n FROM ticker_card WHERE in_watchlist=1")
    return int(df.iloc[0]["n"]) if not df.empty else 0


# ══════════════════════════════════════════════════════════════════════════════
# Decision Log
# ══════════════════════════════════════════════════════════════════════════════

def get_decision_log_df(symbol: str | None = None, limit: int = 100) -> pd.DataFrame:
    """Decision log, opzionalmente filtrato per symbol."""
    if not table_exists("decision_log"):
        return pd.DataFrame()
    if symbol:
        return query_df(
            "SELECT * FROM decision_log WHERE symbol=:s ORDER BY ts DESC LIMIT :limit",
            {"s": symbol, "limit": limit},
        )
    return query_df(
        "SELECT * FROM decision_log ORDER BY ts DESC LIMIT :limit",
        {"limit": limit},
    )


# ══════════════════════════════════════════════════════════════════════════════
# Market Data (prezzi)
# ══════════════════════════════════════════════════════════════════════════════

def get_price_bars_df(symbol: str, interval: str = "1d", limit: int = 500) -> pd.DataFrame:
    """OHLCV bars per un simbolo."""
    if not table_exists("price_bars"):
        return pd.DataFrame()
    return query_df(
        "SELECT * FROM price_bars WHERE symbol=:s AND interval=:i "
        "ORDER BY ts DESC LIMIT :limit",
        {"s": symbol, "i": interval, "limit": limit},
    )


def get_latest_price(symbol: str) -> float | None:
    """Ultimo prezzo chiusura per un simbolo."""
    df = get_price_bars_df(symbol, limit=1)
    return float(df.iloc[0]["close"]) if not df.empty else None


def get_available_symbols() -> list[str]:
    """Simboli con dati di prezzo nel DB."""
    if not table_exists("price_bars"):
        return []
    df = query_df("SELECT DISTINCT symbol FROM price_bars ORDER BY symbol")
    return df["symbol"].tolist()


def get_benchmark_bars_df(interval: str = "1d", limit: int = 500) -> pd.DataFrame:
    """Prezzi benchmark (SPY)."""
    if not table_exists("price_bars"):
        return pd.DataFrame()
    return query_df(
        "SELECT * FROM price_bars WHERE symbol='SPY' AND interval=:i "
        "ORDER BY ts ASC LIMIT :limit",
        {"i": interval, "limit": limit},
    )


# ══════════════════════════════════════════════════════════════════════════════
# News & Social
# ══════════════════════════════════════════════════════════════════════════════

def get_recent_news(symbol: str | None = None, limit: int = 50) -> pd.DataFrame:
    if not table_exists("news_items"):
        return pd.DataFrame()
    if symbol:
        return query_df(
            "SELECT * FROM news_items WHERE symbol=:s ORDER BY ts DESC LIMIT :limit",
            {"s": symbol, "limit": limit},
        )
    return query_df(
        "SELECT * FROM news_items ORDER BY ts DESC LIMIT :limit",
        {"limit": limit},
    )


# ══════════════════════════════════════════════════════════════════════════════
# Stats / System State
# ══════════════════════════════════════════════════════════════════════════════

def get_cycles_count() -> int:
    """Numero di cicli eseguiti (giorni distinti nel decision log)."""
    if not table_exists("decision_log"):
        return 0
    df = query_df("SELECT COUNT(DISTINCT DATE(ts)) as n FROM decision_log")
    return int(df.iloc[0]["n"]) if not df.empty else 0


def get_db_path() -> str:
    return str(_DEFAULT_DB)


def db_exists() -> bool:
    return _DEFAULT_DB.exists()
