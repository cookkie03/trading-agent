"""Ticker analysis page — single symbol deep-dive."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from tradingagents.dashboard.components.metrics import section_header
from tradingagents.dashboard.db_reader import (
    get_available_symbols,
    get_price_bars_df,
    get_decision_log_df,
    get_recent_news,
)


def page_ticker() -> None:
    st.title("📈 Analisi Ticker")

    symbols = get_available_symbols()
    if not symbols:
        st.info("Nessun simbolo nel DB.")
        return

    selected = st.selectbox("Seleziona simbolo", symbols)
    if not selected:
        return

    bars = get_price_bars_df(selected, limit=500)
    if bars.empty:
        st.info(f"Nessun dato di prezzo per {selected}")
        return

    bars_sorted = bars.sort_values("ts")

    # ── Prezzo ───────────────────────────────────────────────────────────
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=bars_sorted["ts"],
        open=bars_sorted["open"],
        high=bars_sorted["high"],
        low=bars_sorted["low"],
        close=bars_sorted["close"],
        name=selected,
    ))
    # Volume
    if "volume" in bars_sorted.columns:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=bars_sorted["ts"], y=bars_sorted["volume"],
            name="Volume", marker_color="rgba(99,102,241,0.4)",
        ))
        fig2.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=5, b=0),
            height=120,
            showlegend=False,
            xaxis=dict(gridcolor="rgba(99,102,241,0.05)"),
            yaxis=dict(gridcolor="rgba(99,102,241,0.05)"),
        )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=10, b=0),
        height=450,
        xaxis_rangeslider_visible=False,
        xaxis=dict(gridcolor="rgba(99,102,241,0.05)"),
        yaxis=dict(gridcolor="rgba(99,102,241,0.05)"),
    )
    st.plotly_chart(fig, use_container_width=True)
    if "volume" in bars_sorted.columns and not bars_sorted["volume"].isna().all():
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=bars_sorted["ts"], y=bars_sorted["volume"],
            name="Volume", marker_color="rgba(99,102,241,0.4)",
        ))
        fig2.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=5, b=0),
            height=120,
            showlegend=False,
            xaxis=dict(gridcolor="rgba(99,102,241,0.05)"),
            yaxis=dict(gridcolor="rgba(99,102,241,0.05)"),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Decisioni per questo ticker ──────────────────────────────────────
    decisions = get_decision_log_df(symbol=selected, limit=20)
    if not decisions.empty:
        section_header(f"Decisioni — {selected}")
        dec_cols = ["ts", "direction", "conviction", "risk_verdict", "traded"]
        available = [c for c in dec_cols if c in decisions.columns]
        st.dataframe(decisions[available], use_container_width=True, hide_index=True)

    # ── News ─────────────────────────────────────────────────────────────
    news = get_recent_news(symbol=selected, limit=10)
    if not news.empty:
        section_header(f"News — {selected}")
        for _, row in news.iterrows():
            ts = row.get("ts", "")
            headline = row.get("headline", "")
            source = row.get("source", "")
            with st.expander(f"{ts} — {headline[:80]}"):
                st.write(headline)
                if source:
                    st.caption(f"Fonte: {source}")
