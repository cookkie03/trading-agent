"""Overview / Dashboard page — KPI cards, NAV chart, drawdown, recent trades."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from tradingagents.dashboard.components.metrics import (
    fmt_num,
    fmt_pct,
    render_kpi_grid,
    section_header,
)
from tradingagents.dashboard.db_reader import (
    get_latest_portfolio,
    get_portfolio_history,
    get_trades_df,
    get_open_trades,
    get_benchmark_bars_df,
)
from tradingagents.dashboard.metrics import (
    sharpe_ratio,
    max_drawdown,
    calmar_ratio,
    annualized_volatility,
    drawdown_series,
)


def page_dashboard() -> None:
    st.title("📊 Dashboard")

    latest = get_latest_portfolio()
    if not latest:
        st.warning("Nessun dato nel DB. Avvia il trading-agent per popolare il DB.")
        return

    # ── KPI Cards ────────────────────────────────────────────────────────
    nav_hist = get_portfolio_history()
    if not nav_hist.empty and "total_value" in nav_hist.columns:
        nav_series = nav_hist.sort_values("ts")["total_value"]
        current = float(nav_series.iloc[-1])
        initial = float(nav_series.iloc[0]) if nav_series.iloc[0] > 0 else current
        since_incep = (current / initial - 1) if initial > 0 else 0
        sharpe = sharpe_ratio(nav_series)
        mdd = max_drawdown(nav_series)
        calmar = calmar_ratio(nav_series)
        vol = annualized_volatility(nav_series)
    else:
        current = latest.get("total_value", 0)
        initial = current
        since_incep = 0
        sharpe = mdd = calmar = vol = 0

    trades_df = get_trades_df()
    n_trades = len(trades_df) if not trades_df.empty else 0
    open_trades_df = get_open_trades()
    n_open = len(open_trades_df) if not open_trades_df.empty else 0

    render_kpi_grid([
        {"label": "NAV Corrente", "value": fmt_num(current, prefix="$ "), "accent": "purple"},
        {"label": "Since Inception", "value": fmt_pct(since_incep), "delta": fmt_pct(since_incep), "accent": "green"},
        {"label": "Sharpe Ratio", "value": fmt_num(sharpe), "accent": "blue"},
        {"label": "Max Drawdown", "value": fmt_pct(mdd), "delta": fmt_pct(mdd), "accent": "amber"},
        {"label": "Volatilità Ann.", "value": fmt_pct(vol), "accent": "purple"},
        {"label": "Calmar Ratio", "value": fmt_num(calmar), "accent": "green"},
        {"label": "Trade Totali", "value": str(n_trades), "accent": "blue"},
        {"label": "Posizioni Aperte", "value": str(n_open), "accent": "amber"},
    ])

    # ── NAV Chart ────────────────────────────────────────────────────────
    section_header("NAV vs Benchmark")
    if not nav_hist.empty and "total_value" in nav_hist.columns:
        nav_sorted = nav_hist.sort_values("ts")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=nav_sorted["ts"], y=nav_sorted["total_value"],
            name="NAV", line=dict(color="#6366f1", width=2),
            fill="tozeroy", fillcolor="rgba(99,102,241,0.05)",
        ))
        # Benchmark
        bench = get_benchmark_bars_df()
        if not bench.empty and "close" in bench.columns:
            bench_sorted = bench.sort_values("ts")
            bench_norm = bench_sorted["close"] / bench_sorted["close"].iloc[0] * initial
            fig.add_trace(go.Scatter(
                x=bench_sorted["ts"], y=bench_norm,
                name="SPY (norm)", line=dict(color="#f59e0b", width=1.5, dash="dot"),
            ))
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=0),
            height=350,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            xaxis=dict(gridcolor="rgba(99,102,241,0.05)"),
            yaxis=dict(gridcolor="rgba(99,102,241,0.05)"),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Drawdown ─────────────────────────────────────────────────────────
    section_header("Drawdown")
    if not nav_hist.empty and "total_value" in nav_hist.columns:
        nav_series = nav_hist.sort_values("ts")["total_value"]
        dd = drawdown_series(nav_series)
        dd.index = pd.to_datetime(nav_hist.sort_values("ts")["ts"])
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dd.index, y=dd.values * 100,
            fill="tozeroy", fillcolor="rgba(239,68,68,0.15)",
            line=dict(color="#ef4444", width=1), name="Drawdown",
        ))
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=0),
            height=200,
            showlegend=False,
            xaxis=dict(gridcolor="rgba(99,102,241,0.05)"),
            yaxis=dict(gridcolor="rgba(99,102,241,0.05)", ticksuffix="%"),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Recent Trades ────────────────────────────────────────────────────
    section_header("Ultimi Trade")
    if not trades_df.empty:
        display_cols = ["ts", "symbol", "action", "quantity", "entry_price", "status", "exit_reason"]
        available = [c for c in display_cols if c in trades_df.columns]
        st.dataframe(
            trades_df[available].head(20).style.format({
                "entry_price": "{:.2f}",
                "quantity": "{:.2f}",
            }),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Nessun trade registrato")
