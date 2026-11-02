"""Deterministic desk contributions over normalized research inputs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from analysis.strategy_state import ResearchState
from data.providers.alpaca_news import NewsItem


@dataclass(frozen=True)
class DeskContext:
    symbol: str
    as_of: date
    current_price: Decimal
    research: ResearchState
    news: tuple[NewsItem, ...] = ()


@dataclass(frozen=True)
class DeskOpinion:
    desk: str
    view: str
    rationale: str
    evidence: tuple[str, ...]


def run_desks(context: DeskContext) -> tuple[DeskOpinion, ...]:
    """Run the four required desk seams without external calls or invented data."""
    return (
        DeskOpinion(
            desk="market",
            view="market context pending provider evidence",
            rationale="Macro and sector data must come from a connected provider.",
            evidence=(),
        ),
        DeskOpinion(
            desk="technical",
            view=context.research.technical_view,
            rationale="Technical view is supplied by the normalized quantitative context.",
            evidence=("atr", "quantitative evaluation"),
        ),
        DeskOpinion(
            desk="fundamentals",
            view="fundamentals context pending provider evidence",
            rationale="Earnings and valuation claims require cited fundamental observations.",
            evidence=(),
        ),
        DeskOpinion(
            desk="sentiment",
            view=(
                "; ".join(item.headline for item in context.news)
                if context.news
                else "sentiment context pending provider evidence"
            ),
            rationale="News headlines are observations, not inferred sentiment or positioning.",
            evidence=tuple(
                f"{item.source} | {item.published_at.isoformat()} | {item.url}"
                for item in context.news
            ),
        ),
    )
