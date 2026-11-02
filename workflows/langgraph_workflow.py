"""Minimal LangGraph adapter around the deterministic risk analyst."""

from __future__ import annotations

from decimal import Decimal
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from agents.risk import RiskAnalyst, RiskReview
from analysis.strategy_state import ResearchState
from execution.risk import PortfolioRisk, RiskLimits


class ResearchGraphState(TypedDict, total=False):
    research: ResearchState
    portfolio: dict[str, Decimal]
    limits: dict[str, Decimal]
    entry_price: Decimal
    risk_review: RiskReview


def _risk_node(state: ResearchGraphState) -> dict[str, RiskReview]:
    portfolio = PortfolioRisk(**state["portfolio"])
    limits = RiskLimits(**state["limits"])
    review = RiskAnalyst(limits).review(
        state["research"],
        portfolio,
        state["entry_price"],
    )
    return {"risk_review": review}


def build_research_graph():
    graph = StateGraph(ResearchGraphState)
    graph.add_node("risk_review", _risk_node)
    graph.add_edge(START, "risk_review")
    graph.add_edge("risk_review", END)
    return graph.compile()
