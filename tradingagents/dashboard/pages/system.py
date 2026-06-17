"""System status page — DB info, stats, daemon logs."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from tradingagents.dashboard.db_reader import (
    db_exists,
    get_db_path,
    get_latest_portfolio,
    get_universe_size,
    get_watchlist_size,
    get_cycles_count,
    get_trades_df,
)


def page_system() -> None:
    st.title("⚙️ Stato Sistema")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Database")
        st.caption(f"Path: `{get_db_path()}`")
        st.caption(f"Esiste: {'✅' if db_exists() else '❌'}")

        latest = get_latest_portfolio()
        if latest:
            st.json({
                "NAV": latest.get("total_value"),
                "Cash": latest.get("cash"),
                "Timestamp": str(latest.get("ts")),
                "Posizioni": len(latest.get("positions", [])),
            })

    with col2:
        st.subheader("Statistiche")
        st.metric("Universo", get_universe_size())
        st.metric("Watchlist", get_watchlist_size())
        st.metric("Cicli", get_cycles_count())

        trades = get_trades_df()
        if not trades.empty:
            st.metric("Trade Totali", len(trades))
            if "status" in trades.columns:
                status_counts = trades["status"].value_counts()
                st.bar_chart(status_counts)

    # ── Log file ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Log del Daemon")
    log_path = Path.home() / ".tradingagents" / "agent.log"
    if log_path.exists():
        with open(log_path) as f:
            lines = f.readlines()
        st.text("".join(lines[-100:]))
    else:
        st.info("Log file non trovato. Avvia il daemon con `cli start`.")
