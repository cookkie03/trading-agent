"""Minimal LangGraph adapter around the deterministic risk analyst."""

from __future__ import annotations

from decimal import Decimal
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from agents.desks import DeskContext, DeskOpinion, run_desks
from agents.risk import RiskAnalyst, RiskReview
from analysis.strategy_state import ResearchState
from data.models import PriceBar
from data.providers.alpaca_news import NewsItem
from data.providers.yahoo_fundamentals import FundamentalObservation
from execution.risk import PortfolioRisk, RiskLimits


class ResearchGraphState(TypedDict, total=False):
    research: ResearchState
    portfolio: dict[str, Decimal]
    limits: dict[str, Decimal]
    entry_price: Decimal
    technical_complete: bool
    news: tuple[NewsItem, ...]
    fundamentals: tuple[FundamentalObservation, ...]
    market_bar: PriceBar | None
    desk_opinions: tuple[DeskOpinion, ...]
    pm_ready: bool
    pm_review: dict
    risk_review: RiskReview
    decision: str


def _desk_node(state: ResearchGraphState) -> dict[str, tuple[DeskOpinion, ...]]:
    research = state["research"]
    return {
        "desk_opinions": run_desks(
            DeskContext(
                symbol=research.symbol,
                as_of=research.as_of,
                current_price=state["entry_price"],
                research=research,
                news=state.get("news", ()),
                fundamentals=state.get("fundamentals", ()),
                market_bar=state.get("market_bar"),
            )
        )
    }


def _pm_node(state: ResearchGraphState) -> dict[str, bool]:
    # Evidence availability is not a PM thesis or a decision to trade.
    return {"pm_ready": False}


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
    if not review.approved:
        return {"decision": "rejected"}
    return {
        "decision": "approved" if state["pm_ready"] and state["technical_complete"] else "pending"
    }


def build_research_graph(*, checkpointer=None, pm_reviewer=None):
    graph = StateGraph(ResearchGraphState)
    graph.add_node("desk_review", _desk_node)

    def pm_node(state):
        if pm_reviewer is None:
            return _pm_node(state)
        try:
            review = pm_reviewer(state["research"], state["desk_opinions"])
        except Exception:
            return {"pm_ready": False}
        if not isinstance(review, dict):
            return {"pm_ready": False}
        citations = review.get("evidence")
        if not isinstance(citations, list) or not all(isinstance(x, str) for x in citations):
            return {"pm_ready": False}
        opinions = state["desk_opinions"]
        available = {item for opinion in opinions for item in opinion.evidence}
        ready = (
            review.get("run_id") == state["research"].run_id
            and review.get("symbol") == state["research"].symbol
            and review.get("decision") == "approve"
            and all(
                isinstance(review.get(key), str) and review[key].strip()
                for key in ("thesis", "counter_thesis", "uncertainties")
            )
            and bool(opinions)
            and all(
                opinion.evidence and any(x in opinion.evidence for x in citations)
                for opinion in opinions
            )
            and len(citations) == len(set(citations))
            and set(citations) <= available
        )
        return {"pm_ready": bool(ready), "pm_review": review}

    graph.add_node("pm_review", pm_node)
    graph.add_node("technical_review", _technical_node)
    graph.add_node("risk_review", _risk_node)
    graph.add_node("decision", _decision_node)
    graph.add_edge(START, "desk_review")
    graph.add_edge("desk_review", "pm_review")
    graph.add_edge("pm_review", "technical_review")
    graph.add_edge("technical_review", "risk_review")
    graph.add_edge("risk_review", "decision")
    graph.add_edge("decision", END)
    return graph.compile(checkpointer=checkpointer)
