"""Shared formatting helpers and KPI card components."""

from __future__ import annotations

import streamlit as st


# ── Formatters ────────────────────────────────────────────────────────────────


def fmt_pct(v: float | None, decimals: int = 2) -> str:
    """Format a float as percentage string (e.g. 0.15 → '15.00%')."""
    if v is None:
        return "N/A"
    return f"{v * 100:.{decimals}f}%"


def fmt_num(v: float | None, decimals: int = 2, prefix: str = "") -> str:
    """Format a float with thousands separator and optional prefix."""
    if v is None:
        return "N/A"
    return f"{prefix}{v:,.{decimals}f}"


# ── KPI Cards ─────────────────────────────────────────────────────────────────


def kpi_card(label: str, value: str, delta: str | None = None, accent: str = "purple") -> str:
    """Return HTML for a single KPI card."""
    delta_html = ""
    if delta:
        cls = "pos" if not delta.startswith("-") else "neg"
        delta_html = f'<div class="kpi-delta"><span class="{cls}">{delta}</span></div>'
    return f'<div class="kpi-card accent-{accent}"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div>{delta_html}</div>'


def render_kpi_grid(cards: list[dict]) -> None:
    """Render a grid of KPI cards. Each dict: {label, value, delta?, accent?}."""
    html = '<div class="kpi-grid">'
    for c in cards:
        html += kpi_card(
            c["label"], c["value"], c.get("delta"), c.get("accent", "purple")
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ── Section Headers ───────────────────────────────────────────────────────────


def section_header(title: str) -> None:
    """Render a styled section header."""
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)
