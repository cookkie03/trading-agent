"""
Trading-Agent Observability Dashboard
=======================================
Read-only dashboard. Legge dal DB SQLite del trading-agent.

Run:
    streamlit run tradingagents/dashboard/app.py
    oppure:
    python -m tradingagents.dashboard.app
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Local imports ────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tradingagents.dashboard.db_reader import (
    db_exists,
    get_db_path,
    get_latest_portfolio,
    get_portfolio_history,
    get_trades_df,
    get_open_trades,
    get_watchlist_df,
    get_universe_size,
    get_watchlist_size,
    get_decision_log_df,
    get_recent_research_states,
    get_price_bars_df,
    get_available_symbols,
    get_benchmark_bars_df,
    get_recent_news,
    get_cycles_count,
    get_ticker_card,
)
from tradingagents.dashboard.metrics import (
    total_return,
    annualized_return,
    annualized_volatility,
    sharpe_ratio,
    sortino_ratio,
    max_drawdown,
    drawdown_series,
    calmar_ratio,
    var_historical,
    cvar_historical,
    compute_alpha_beta,
)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG & DARK THEME CSS (ispirato a SFC portfolio tracker)
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Trading-Agent Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    .main .block-container {
        padding-top: 0.5rem; max-width: 1600px;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    #MainMenu, footer { visibility: hidden; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #080810 0%, #0d0d1a 100%);
        border-right: 1px solid rgba(99,102,241,0.12);
    }

    /* ── KPI Cards ── */
    .kpi-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:0.7rem; margin-bottom:0.8rem; }
    @media(max-width:768px){ .kpi-grid{grid-template-columns:repeat(2,1fr);} }
    .kpi-card {
        background: linear-gradient(135deg, #0d0d1a 0%, #13132a 100%);
        border: 1px solid rgba(99,102,241,0.10); border-radius:10px;
        padding: 0.9rem 1.1rem; transition: border-color 0.2s;
    }
    .kpi-card:hover { border-color: rgba(99,102,241,0.3); }
    .kpi-label { font-size:0.65rem; font-weight:600; color:#64748b; text-transform:uppercase; letter-spacing:0.8px; margin-bottom:0.35rem; }
    .kpi-value { font-size:1.45rem; font-weight:700; color:#e2e8f0; line-height:1.2; }
    .kpi-delta { font-size:0.72rem; font-weight:500; margin-top:0.25rem; color:#64748b; }
    .pos { color:#22c55e !important; font-weight:600; }
    .neg { color:#ef4444 !important; font-weight:600; }
    .accent-purple { border-left:3px solid #6366f1; }
    .accent-green { border-left:3px solid #22c55e; }
    .accent-blue { border-left:3px solid #3b82f6; }
    .accent-amber { border-left:3px solid #f59e0b; }

    /* ── Section Headers ── */
    .section-header {
        font-size:0.8rem; font-weight:600; color:#94a3b8; text-transform:uppercase;
        letter-spacing:0.8px; margin:1.2rem 0 0.5rem; padding-bottom:0.4rem;
        border-bottom:1px solid rgba(99,102,241,0.10);
    }

    /* ── Streamlit Overrides ── */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #0d0d1a 0%, #13132a 100%);
        border:1px solid rgba(99,102,241,0.08); border-radius:10px; padding:0.7rem 0.9rem;
    }
    [data-testid="stMetricLabel"] { font-size:0.68rem !important; text-transform:uppercase; letter-spacing:0.4px; }
    [data-testid="stExpander"] {
        border:1px solid rgba(99,102,241,0.08); border-radius:10px; background:rgba(13,13,26,0.3);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap:0.2rem; background:rgba(13,13,26,0.6); padding:0.25rem;
        border-radius:10px; border:1px solid rgba(99,102,241,0.08);
    }
    .stTabs [data-baseweb="tab"] { border-radius:8px; padding:0.4rem 1rem; font-weight:500; font-size:0.8rem; }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width:5px; }
    ::-webkit-scrollbar-track { background:#0a0a14; }
    ::-webkit-scrollbar-thumb { background:#2a2a4a; border-radius:3px; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def fmt_pct(v: float | None, decimals: int = 2) -> str:
    if v is None:
        return "N/A"
    return f"{v*100:.{decimals}f}%"


def fmt_num(v: float | None, decimals: int = 2, prefix: str = "") -> str:
    if v is None:
        return "N/A"
    return f"{prefix}{v:,.{decimals}f}"


def kpi_card(label: str, value: str, delta: str | None = None, accent: str = "purple") -> str:
    delta_html = ""
    if delta:
        cls = "pos" if not delta.startswith("-") else "neg"
        delta_html = f'<div class="kpi-delta"><span class="{cls}">{delta}</span></div>'
    return f"""
    <div class="kpi-card accent-{accent}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """


def render_kpi_grid(cards: list[dict]):
    """Renderizza una griglia di KPI card. Ogni dict: {label, value, delta?, accent?}"""
    html = '<div class="kpi-grid">'
    for c in cards:
        html += kpi_card(
            c["label"], c["value"], c.get("delta"), c.get("accent", "purple")
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def section_header(title: str):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

def render_sidebar():
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


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD (overview)
# ══════════════════════════════════════════════════════════════════════════════

def page_dashboard():
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


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: WATCHLIST & TICKER CARDS
# ══════════════════════════════════════════════════════════════════════════════

def page_watchlist():
    st.title("📋 Watchlist & Ticker Cards")

    wl = get_watchlist_df()
    if wl.empty:
        st.info("Watchlist vuota. Il sistema la popolerà al primo ciclo.")
        return

    # Summary
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Watchlist", len(wl))
    col2.metric("In Portfolio", int(wl["in_portfolio"].sum()) if "in_portfolio" in wl.columns else 0)
    scored = wl["screening_score"].dropna() if "screening_score" in wl.columns else pd.Series(dtype=float)
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


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DECISIONI & RESEARCH STATES
# ══════════════════════════════════════════════════════════════════════════════

def page_decisions():
    st.title("🧠 Decisioni & Research States")

    tab1, tab2 = st.tabs(["Decision Log", "Research States"])

    with tab1:
        decisions = get_decision_log_df(limit=100)
        if decisions.empty:
            st.info("Nessuna decisione registrata.")
        else:
            # Filtri
            col1, col2 = st.columns(2)
            with col1:
                if "symbol" in decisions.columns:
                    symbols = ["Tutti"] + sorted(decisions["symbol"].dropna().unique().tolist())
                    sel_sym = st.selectbox("Filtra per simbolo", symbols)
                    if sel_sym != "Tutti":
                        decisions = decisions[decisions["symbol"] == sel_sym]
            with col2:
                if "traded" in decisions.columns:
                    only_traded = st.checkbox("Solo eseguiti", value=False)
                    if only_traded:
                        decisions = decisions[decisions["traded"] == True]

            display_cols = ["ts", "symbol", "direction", "conviction", "risk_verdict", "traded"]
            available = [c for c in display_cols if c in decisions.columns]
            st.dataframe(decisions[available], use_container_width=True, hide_index=True)

            # Dettaglio decisione
            st.markdown("---")
            st.subheader("Dettaglio Decisione")
            if "id" in decisions.columns and len(decisions) > 0:
                sel_id = st.selectbox("Seleziona decisione", decisions["id"].tolist(),
                                      format_func=lambda x: f"#{x}")
                row = decisions[decisions["id"] == sel_id]
                if not row.empty:
                    r = row.iloc[0]
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Symbol", r.get("symbol", "N/A"))
                    c2.metric("Direction", r.get("direction", "N/A"))
                    c3.metric("Conviction", r.get("conviction", "N/A"))
                    c4.metric("Risk Verdict", r.get("risk_verdict", "N/A"))

                    # Agent opinions
                    if "agent_opinions" in r and r["agent_opinions"]:
                        st.markdown("**Opinioni Agenti:**")
                        try:
                            opinions = r["agent_opinions"] if isinstance(r["agent_opinions"], list) else json.loads(r["agent_opinions"])
                            for op in opinions:
                                st.markdown(f"- **{op.get('agent', '?')}**: {op.get('suggested_direction', '?')} — {op.get('rationale', '')[:200]}")
                        except Exception:
                            st.json(r["agent_opinions"])

                    # Payload completo
                    with st.expander("Payload completo"):
                        payload = r.get("payload", {})
                        if isinstance(payload, str):
                            try:
                                payload = json.loads(payload)
                            except Exception:
                                pass
                        st.json(payload)

    with tab2:
        states = get_recent_research_states(limit=50)
        if states.empty:
            st.info("Nessuno stato di ricerca.")
        else:
            display_cols = ["created_at", "symbol", "direction", "conviction", "status"]
            available = [c for c in display_cols if c in states.columns]
            st.dataframe(states[available], use_container_width=True, hide_index=True)

            # Dettaglio
            if "id" in states.columns and len(states) > 0:
                st.markdown("---")
                sel_state = st.selectbox("Seleziona stato", states["id"].tolist(),
                                         format_func=lambda x: f"#{x}")
                row = states[states["id"] == sel_state]
                if not row.empty:
                    r = row.iloc[0]
                    payload = r.get("payload", {})
                    if isinstance(payload, str):
                        try:
                            payload = json.loads(payload)
                        except Exception:
                            pass
                    st.json(payload)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: TRADE DETAIL
# ══════════════════════════════════════════════════════════════════════════════

def page_trades():
    st.title("💹 Trades")

    trades = get_trades_df()
    if trades.empty:
        st.info("Nessun trade registrato.")
        return

    # Summary
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Totali", len(trades))
    filled = trades[trades["status"] == "filled"] if "status" in trades.columns else pd.DataFrame()
    col2.metric("Eseguiti", len(filled))
    cancelled = trades[trades["status"] == "cancelled"] if "status" in trades.columns else pd.DataFrame()
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


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: PER TICKER (analisi singolo simbolo)
# ══════════════════════════════════════════════════════════════════════════════

def page_ticker():
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


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SYSTEM STATUS
# ══════════════════════════════════════════════════════════════════════════════

def page_system():
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


# ══════════════════════════════════════════════════════════════════════════════
# MAIN — PAGE ROUTER
# ══════════════════════════════════════════════════════════════════════════════

PAGES = {
    "📊 Dashboard": page_dashboard,
    "📋 Watchlist": page_watchlist,
    "🧠 Decisioni": page_decisions,
    "💹 Trades": page_trades,
    "📈 Ticker": page_ticker,
    "⚙️ Sistema": page_system,
}


def main():
    if not render_sidebar():
        return

    st.markdown("---")
    page_names = list(PAGES.keys())
    selected_page = st.radio("Naviga", page_names, horizontal=True, label_visibility="collapsed")
    st.markdown("---")

    PAGES[selected_page]()


if __name__ == "__main__":
    main()
