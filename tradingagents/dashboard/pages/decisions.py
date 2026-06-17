"""Decisions & Research States page."""

from __future__ import annotations

import json

import streamlit as st

from tradingagents.dashboard.db_reader import (
    get_decision_log_df,
    get_recent_research_states,
)


def page_decisions() -> None:
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
