"""Watchlist & Ticker Cards page."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from tradingagents.dashboard.components.metrics import section_header
from tradingagents.dashboard.db_reader import (
    get_watchlist_df,
    get_ticker_card,
    get_price_bars_df,
    get_decision_log_df,
)


def page_watchlist() -> None:
    st.title("📋 Watchlist & Ticker Cards")

    wl = get_watchlist_df()
    if wl.empty:
        st.info("Watchlist vuota. Il sistema la popolerà al primo ciclo.")
        return

    # Summary
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Watchlist", len(wl))
    col2.metric("In Portfolio", int(wl["in_portfolio"].sum()) if "in_portfolio" in wl.columns else 0)
    scored = wl["screening_score"].dropna() if "screening_score" in wl.columns else __import__("pandas").Series(dtype=float)
    col3.metric("Avg Score", f"{scored.mean():.3f}" if len(scored) > 0 else "N/A")
    col4.metric("Con Direction", len(wl[wl["latest_direction"].notna()]) if "latest_direction" in wl.columns else 0)

    st.markdown("---")

    # Tabella watchlist
    st.subheader("Watchlist")
    display_cols = ["symbol", "screening_score", "latest_direction", "latest_conviction",
                    "next_check_date", "in_portfolio", "watchlist_reason"]
    available = [c for c in display_cols if c in wl.columns]
    st.dataframe(
        wl[available].sort_values("screening_score", ascending=False).style.format({
            "screening_score": "{:.3f}",
        }),
        use_container_width=True,
        hide_index=True,
    )

    # ── Dettaglio ticker ─────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Dettaglio Ticker")
    symbols = wl["symbol"].tolist() if "symbol" in wl.columns else []
    if symbols:
        selected = st.selectbox("Seleziona ticker", symbols)
        if selected:
            col1, col2 = st.columns([1, 2])
            with col1:
                card = get_ticker_card(selected)
                if card:
                    st.json(card)
            with col2:
                bars = get_price_bars_df(selected, limit=252)
                if not bars.empty and "close" in bars.columns:
                    bars_sorted = bars.sort_values("ts")
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=bars_sorted["ts"],
                        open=bars_sorted["open"],
                        high=bars_sorted["high"],
                        low=bars_sorted["low"],
                        close=bars_sorted["close"],
                        name=selected,
                    ))
                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        margin=dict(l=0, r=0, t=10, b=0),
                        height=400,
                        xaxis_rangeslider_visible=False,
                        xaxis=dict(gridcolor="rgba(99,102,241,0.05)"),
                        yaxis=dict(gridcolor="rgba(99,102,241,0.05)"),
                    )
                    st.plotly_chart(fig, use_container_width=True)

            # Decision log per ticker
            decisions = get_decision_log_df(symbol=selected, limit=20)
            if not decisions.empty:
                st.subheader(f"Decision Log — {selected}")
                dec_cols = ["ts", "direction", "conviction", "risk_verdict", "traded"]
                available_dec = [c for c in dec_cols if c in decisions.columns]
                st.dataframe(decisions[available_dec], use_container_width=True, hide_index=True)
