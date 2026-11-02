"""Pure assembly of a draft research thesis from desk inputs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from analysis.strategy_state import (
    Conviction,
    Direction,
    QuantitativeEvaluation,
    ResearchState,
    StrategyProfile,
)


@dataclass(frozen=True)
class ResearchInputs:
    run_id: str
    symbol: str
    as_of: date
    profile: StrategyProfile
    evaluations: tuple[QuantitativeEvaluation, ...]
    market_context: str
    technical_view: str
    bull_case: tuple[str, ...]
    bear_case: tuple[str, ...]
    invalidation_conditions: tuple[str, ...]
    proposed_direction: Direction
    conviction: Conviction
    next_check_date: date


def build_research_state(inputs: ResearchInputs) -> ResearchState:
    """Build an unapproved state; only risk analysis can approve it later."""
    return ResearchState(
        run_id=inputs.run_id,
        symbol=inputs.symbol,
        as_of=inputs.as_of,
        profile=inputs.profile,
        evaluations=inputs.evaluations,
        market_context=inputs.market_context,
        technical_view=inputs.technical_view,
        bull_case=inputs.bull_case,
        bear_case=inputs.bear_case,
        invalidation_conditions=inputs.invalidation_conditions,
        proposed_direction=inputs.proposed_direction,
        conviction=inputs.conviction,
        next_check_date=inputs.next_check_date,
        status="draft",
    )
