"""Shared sidebar component."""

from __future__ import annotations

import streamlit as st

from tradingagents.dashboard.components.metrics import fmt_num
from tradingagents.dashboard.db_reader import (
    db_exists,
    get_db_path,
    get_latest_portfolio,
    get_universe_size,
    get_watchlist_size,
    get_cycles_count,
)


def render_sidebar() -> bool:
    """Render the sidebar. Returns False if the DB is not available."""
    with st.sidebar:
        st.markdown("## 🤖 Trading-Agent")
        st.markdown("---")

        if not db_exists():
            st.error("⚠️ DB non trovato")
            st.caption(f"Cercato in: `{get_db_path()}`")
            st.caption("Avvia il trading-agent almeno una volta per popolare il DB.")
            return False

        # System state
        latest = get_latest_portfolio()
        if latest:
            st.metric("NAV", fmt_num(latest.get("total_value"), prefix="$ "))
            st.metric("Cash", fmt_num(latest.get("cash"), prefix="$ "))

        st.markdown("---")
        st.caption(f"DB: `{get_db_path()}`")
        st.caption(f"Universo: {get_universe_size()} simboli")
        st.caption(f"Watchlist: {get_watchlist_size()} simboli")
        st.caption(f"Cicli: {get_cycles_count()}")

        return True
