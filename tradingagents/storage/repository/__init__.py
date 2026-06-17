from __future__ import annotations

from .instrument import (
    bulk_upsert_instruments,
    list_universe,
    mark_instruments_inactive,
    sp500_symbols,
    universe_symbols,
    upsert_instrument,
)
from .ticker import (
    get_ticker_card,
    list_watchlist,
    set_watchlist,
    top_screened,
    upsert_ticker_card,
    watchlist_size,
    watchlist_symbols,
)
from .events import (
    add_ticker_event,
    due_events,
    mark_events_consumed,
)
from .research import (
    latest_research_state,
    save_research_state,
)
from .market import (
    existing_macro_ts,
    existing_news_keys,
    existing_social_keys,
    first_price_on_or_after,
    insert_macro_points,
    insert_news_items,
    insert_price_bars,
    insert_social_posts,
    latest_fundamentals,
    latest_macro,
    latest_price,
    recent_news,
    recent_social,
    save_fundamentals,
)
from .portfolio import (
    first_portfolio_snapshot_on_or_after,
    latest_portfolio_snapshot,
    save_portfolio_snapshot,
)
from .trades import (
    instrument_sector,
    open_trades,
    record_trade,
    sector_exposure,
    trade_by_client_order_id,
)
from .charter import (
    log_decision,
    recent_decisions,
    set_charter_rule,
)

__all__ = [
    # instrument
    "upsert_instrument",
    "bulk_upsert_instruments",
    "list_universe",
    "universe_symbols",
    "mark_instruments_inactive",
    "sp500_symbols",
    # ticker
    "upsert_ticker_card",
    "get_ticker_card",
    "top_screened",
    "set_watchlist",
    "list_watchlist",
    "watchlist_symbols",
    "watchlist_size",
    # events
    "add_ticker_event",
    "due_events",
    "mark_events_consumed",
    # research
    "save_research_state",
    "latest_research_state",
    # market
    "insert_price_bars",
    "existing_news_keys",
    "insert_news_items",
    "recent_news",
    "existing_macro_ts",
    "insert_macro_points",
    "latest_macro",
    "save_fundamentals",
    "latest_fundamentals",
    "existing_social_keys",
    "insert_social_posts",
    "recent_social",
    "latest_price",
    "first_price_on_or_after",
    # portfolio
    "save_portfolio_snapshot",
    "latest_portfolio_snapshot",
    "first_portfolio_snapshot_on_or_after",
    # trades
    "record_trade",
    "trade_by_client_order_id",
    "open_trades",
    "instrument_sector",
    "sector_exposure",
    # charter
    "log_decision",
    "recent_decisions",
    "set_charter_rule",
]
