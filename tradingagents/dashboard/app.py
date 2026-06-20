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

import sys
from pathlib import Path

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

# ── Page imports ─────────────────────────────────────────────────────────────
from tradingagents.dashboard.views.overview import page_dashboard
from tradingagents.dashboard.views.watchlist import page_watchlist
from tradingagents.dashboard.views.decisions import page_decisions
from tradingagents.dashboard.views.trades import page_trades
from tradingagents.dashboard.views.ticker import page_ticker
from tradingagents.dashboard.views.system import page_system
from tradingagents.dashboard.components.sidebar import render_sidebar

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
        background: #0a0a14;
        border-right: 1px solid rgba(255,255,255,0.05);
    }

    /* ── KPI Cards ── */
    .kpi-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:0.7rem; margin-bottom:0.8rem; }
    @media(max-width:768px){ .kpi-grid{grid-template-columns:repeat(2,1fr);} }
    .kpi-card {
        background: #0a0a14;
        border: 1px solid rgba(255,255,255,0.05); border-radius:10px;
        padding: 0.9rem 1.1rem; transition: border-color 0.2s, background-color 0.2s;
    }
    .kpi-card:hover { border-color: rgba(99,102,241,0.3); background: #0f0f20; }
    .kpi-label { font-size:0.65rem; font-weight:600; color:#94a3b8; text-transform:uppercase; letter-spacing:0.8px; margin-bottom:0.35rem; }
    .kpi-value { font-size:1.45rem; font-weight:700; color:#f1f5f9; line-height:1.2; }
    .kpi-delta { font-size:0.72rem; font-weight:500; margin-top:0.25rem; color:#cbd5e1; }
    .pos { color:#22c55e !important; font-weight:600; }
    .neg { color:#ef4444 !important; font-weight:600; }
    .accent-purple { border-left:3px solid #6366f1; }
    .accent-green { border-left:3px solid #22c55e; }
    .accent-blue { border-left:3px solid #3b82f6; }
    .accent-amber { border-left:3px solid #f59e0b; }

    /* ── Section Headers ── */
    .section-header {
        font-size:0.8rem; font-weight:600; color:#cbd5e1; text-transform:uppercase;
        letter-spacing:0.8px; margin:1.2rem 0 0.5rem; padding-bottom:0.4rem;
        border-bottom:1px solid rgba(255,255,255,0.05);
    }

    /* ── Streamlit Overrides ── */
    [data-testid="stMetric"] {
        background: #0a0a14;
        border: 1px solid rgba(255,255,255,0.05); border-radius:10px; padding:0.7rem 0.9rem;
    }
    [data-testid="stMetricLabel"] { font-size:0.68rem !important; text-transform:uppercase; letter-spacing:0.4px; color: #94a3b8 !important; }
    [data-testid="stMetricValue"] { color: #f1f5f9 !important; }
    [data-testid="stExpander"] {
        border: 1px solid rgba(255,255,255,0.05); border-radius:10px; background:#0a0a14;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap:0.2rem; background:#0a0a14; padding:0.25rem;
        border-radius:10px; border:1px solid rgba(255,255,255,0.05);
    }
    .stTabs [data-baseweb="tab"] { border-radius:8px; padding:0.4rem 1rem; font-weight:500; font-size:0.8rem; }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width:5px; }
    ::-webkit-scrollbar-track { background:#0a0a14; }
    ::-webkit-scrollbar-thumb { background:#2a2a4a; border-radius:3px; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE ROUTER
# ══════════════════════════════════════════════════════════════════════════════

PAGES = {
    "📊 Dashboard": page_dashboard,
    "📋 Watchlist": page_watchlist,
    "🧠 Decisioni": page_decisions,
    "💹 Trades": page_trades,
    "📈 Ticker": page_ticker,
    "⚙️ Sistema": page_system,
}


def main() -> None:
    if not render_sidebar():
        return

    st.markdown("---")
    page_names = list(PAGES.keys())
    selected_page = st.radio("Naviga", page_names, horizontal=True, label_visibility="collapsed")
    st.markdown("---")

    PAGES[selected_page]()


if __name__ == "__main__":
    main()
