"""Deterministic desk contributions over normalized research inputs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from analysis.strategy_state import ResearchState
from data.models import PriceBar
from data.providers.alpaca_news import NewsItem
from data.providers.yahoo_fundamentals import FundamentalObservation


@dataclass(frozen=True)
class DeskContext:
    symbol: str
    as_of: date
    current_price: Decimal
    research: ResearchState
    news: tuple[NewsItem, ...] = ()
    fundamentals: tuple[FundamentalObservation, ...] = ()
    market_bar: PriceBar | None = None


@dataclass(frozen=True)
class DeskOpinion:
    desk: str
    view: str
    rationale: str
    evidence: tuple[str, ...]


class MarketAnalyst:
    def analyze(self, context: DeskContext) -> DeskOpinion:
        return DeskOpinion(
            desk="market",
            view=(
                f"{context.market_bar.symbol} close {context.market_bar.close}"
                if context.market_bar
                else "market context pending provider evidence"
            ),
            rationale="A market proxy price is context, not a complete macro or sector analysis.",
            evidence=(
                (f"{context.market_bar.source} | {context.market_bar.timestamp.isoformat()}",)
                if context.market_bar
                else ()
            ),
        )


class TechnicalAnalyst:
    def analyze(self, context: DeskContext) -> DeskOpinion:
        return DeskOpinion(
            desk="technical",
            view=context.research.technical_view,
            rationale="Technical view is supplied by the normalized quantitative context.",
            evidence=tuple(
                f"{item.name} | {item.source} | {item.formula_version} | "
                f"{item.observed_at.isoformat()}"
                for item in context.research.evaluations
            ),
        )


class FundamentalAnalyst:
    def analyze(self, context: DeskContext) -> DeskOpinion:
        return DeskOpinion(
            desk="fundamentals",
            view=(
                "; ".join(f"{item.metric}: {item.value}" for item in context.fundamentals)
                if context.fundamentals
                else "fundamentals context pending provider evidence"
            ),
            rationale="Current provider observations are not historical financial statements.",
            evidence=tuple(
                f"{item.source} | observed {item.observed_at.isoformat()}"
                for item in context.fundamentals
            ),
        )


class SentimentAnalyst:
    def analyze(self, context: DeskContext) -> DeskOpinion:
        return DeskOpinion(
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
        )


def run_desks(context: DeskContext) -> tuple[DeskOpinion, ...]:
    """Run the four required desk seams without external calls or invented data."""
    return tuple(
        analyst.analyze(context)
        for analyst in (
            MarketAnalyst(),
            TechnicalAnalyst(),
            FundamentalAnalyst(),
            SentimentAnalyst(),
        )
    )
