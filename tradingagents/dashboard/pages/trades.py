"""Trades page — trade list with filters."""

from __future__ import annotations

import streamlit as st

from tradingagents.dashboard.db_reader import get_trades_df


def page_trades() -> None:
    st.title("💹 Trades")

    trades = get_trades_df()
    if trades.empty:
        st.info("Nessun trade registrato.")
        return

    # Summary
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Totali", len(trades))
    filled = trades[trades["status"] == "filled"] if "status" in trades.columns else __import__("pandas").DataFrame()
    col2.metric("Eseguiti", len(filled))
    cancelled = trades[trades["status"] == "cancelled"] if "status" in trades.columns else __import__("pandas").DataFrame()
    col3.metric("Cancellati", len(cancelled))
    if "exit_reason" in trades.columns:
        tp = len(trades[trades["exit_reason"] == "tp"])
        sl = len(trades[trades["exit_reason"] == "sl"])
        col4.metric("TP / SL", f"{tp} / {sl}")

    st.markdown("---")

    # Filtri
    col1, col2 = st.columns(2)
    with col1:
        if "symbol" in trades.columns:
            symbols = ["Tutti"] + sorted(trades["symbol"].dropna().unique().tolist())
            sel = st.selectbox("Simbolo", symbols)
            if sel != "Tutti":
                trades = trades[trades["symbol"] == sel]
    with col2:
        if "status" in trades.columns:
            statuses = ["Tutti"] + sorted(trades["status"].dropna().unique().tolist())
            sel_s = st.selectbox("Status", statuses)
            if sel_s != "Tutti":
                trades = trades[trades["status"] == sel_s]

    display_cols = ["ts", "symbol", "action", "quantity", "entry_price", "stop_loss",
                    "take_profit", "status", "exit_reason", "commission"]
    available = [c for c in display_cols if c in trades.columns]
    st.dataframe(
        trades[available].style.format({
            "entry_price": "{:.2f}",
            "stop_loss": "{:.2f}",
            "take_profit": "{:.2f}",
            "quantity": "{:.4f}",
            "commission": "{:.2f}",
        }),
        use_container_width=True,
        hide_index=True,
    )
