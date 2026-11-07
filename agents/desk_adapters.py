"""Connect deterministic desks to the research graph without inventing freshness."""

from collections.abc import Callable
from datetime import datetime
from typing import Any

from agents.desks import (
    DeskContext,
    FundamentalAnalyst,
    MarketAnalyst,
    SentimentAnalyst,
    TechnicalAnalyst,
)
from agents.graph import Analysis


def desk_adapters(context: DeskContext) -> dict[str, Callable[[dict[str, Any]], Analysis]]:
    """Bind a desk context; graph freshness reflects the oldest contributing source."""

    def adapt(
        analyst: Any, role: str, timestamps: Callable[[], tuple[datetime, ...]]
    ) -> Callable[[dict[str, Any]], Analysis]:
        def analyze(_graph_context: dict[str, Any]) -> Analysis:
            if _graph_context.get("symbol") != context.symbol:
                raise ValueError("desk context symbol does not match graph context")
            dates = timestamps()
            if not dates or any(
                not isinstance(value, datetime) or value.utcoffset() is None for value in dates
            ):
                raise ValueError(f"{role} requires timezone-aware source timestamps")
            opinion = analyst.analyze(context)
            if not opinion.evidence:
                raise ValueError(f"{role} requires source evidence")
            return Analysis(
                role=role,
                observed_at=min(dates),
                content={
                    "view": opinion.view,
                    "rationale": opinion.rationale,
                    "evidence": opinion.evidence,
                },
            )

        return analyze

    return {
        "market": adapt(
            MarketAnalyst(),
            "market",
            lambda: (context.market_bar.timestamp,) if context.market_bar else (),
        ),
        "technical": adapt(
            TechnicalAnalyst(),
            "technical",
            lambda: tuple(item.observed_at for item in context.research.evaluations),
        ),
        "fundamental": adapt(
            FundamentalAnalyst(),
            "fundamental",
            lambda: tuple(item.observed_at for item in context.fundamentals),
        ),
        "sentiment": adapt(
            SentimentAnalyst(),
            "sentiment",
            lambda: tuple(item.published_at for item in context.news),
        ),
    }
