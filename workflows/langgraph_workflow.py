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
    technical_complete: bool
    risk_review: RiskReview
    decision: str


def _technical_node(state: ResearchGraphState) -> dict[str, bool]:
    """Represent the technical desk as a deterministic completeness check."""
    research = state["research"]
    complete = bool(research.evaluations and research.technical_view.strip())
    return {"technical_complete": complete}


def _risk_node(state: ResearchGraphState) -> dict[str, RiskReview]:
    portfolio = PortfolioRisk(**state["portfolio"])
    limits = RiskLimits(**state["limits"])
    review = RiskAnalyst(limits).review(
        state["research"],
        portfolio,
        state["entry_price"],
    )
    return {"risk_review": review}


def _decision_node(state: ResearchGraphState) -> dict[str, str]:
    review = state["risk_review"]
    return {"decision": "approved" if review.approved else "rejected"}


def build_research_graph():
    graph = StateGraph(ResearchGraphState)
    graph.add_node("technical_review", _technical_node)
    graph.add_node("risk_review", _risk_node)
    graph.add_node("decision", _decision_node)
    graph.add_edge(START, "technical_review")
    graph.add_edge("technical_review", "risk_review")
    graph.add_edge("risk_review", "decision")
    graph.add_edge("decision", END)
    return graph.compile()
