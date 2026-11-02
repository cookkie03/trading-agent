from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from analysis.strategy_state import (
    QuantitativeEvaluation,
    ResearchState,
    StrategyProfile,
)


def profile() -> StrategyProfile:
    return StrategyProfile(
        key="trend-following-hourly",
        version="0.1",
        objective="Find liquid US equity trends for swing trading",
        family="trend_following",
        timeframe="1h",
        direction_mode="long_only",
        questions=("Is the trend persistent?",),
        tools=("market_data", "technical_indicators"),
        expected_evidence=("hourly OHLCV", "volatility"),
        constraints=("US equities", "USD", "paper only"),
    )


def evaluation() -> QuantitativeEvaluation:
    return QuantitativeEvaluation(
        name="ema_alignment",
        values={"fast_ema": Decimal("105"), "slow_ema": Decimal("100")},
        observed_at=datetime(2026, 11, 2, 14, tzinfo=UTC),
        source="sqlite:price_bars",
        parameters={"fast_window": 20, "slow_window": 50},
        formula_version="ema-wilder-v1",
        interpretation="fast EMA is above slow EMA",
    )


def test_research_state_keeps_profile_and_quantitative_provenance():
    state = ResearchState(
        run_id="run-1",
        symbol="AAPL",
        as_of=date(2026, 11, 2),
        profile=profile(),
        evaluations=(evaluation(),),
        market_context="US equity, regular session",
        technical_view="Trend is positive",
        bull_case=("EMA alignment",),
        bear_case=("Earnings gap risk",),
        invalidation_conditions=("Close below slow EMA",),
        proposed_direction="long",
        conviction="buy",
        next_check_date=date(2026, 11, 3),
        status="draft",
    )

    assert state.is_complete() is True
    assert state.evaluations[0].formula_version == "ema-wilder-v1"
    assert state.can_be_approved() is False


def test_research_state_requires_risk_approval_before_investment_state():
    state = ResearchState(
        run_id="run-2",
        symbol="AAPL",
        as_of=date(2026, 11, 2),
        profile=profile(),
        evaluations=(evaluation(),),
        market_context="context",
        technical_view="trend",
        bull_case=("support",),
        bear_case=("gap",),
        invalidation_conditions=("breakdown",),
        proposed_direction="long",
        conviction="buy",
        next_check_date=date(2026, 11, 3),
        status="approved",
        risk_verdict="approved",
        risk_rationale="Position is within limits",
    )

    assert state.can_be_approved() is True
    assert state.to_investment_state().status == "approved"


def test_long_only_profile_rejects_short_proposal():
    with pytest.raises(ValueError, match="short"):
        ResearchState(
            run_id="run-3",
            symbol="AAPL",
            as_of=date(2026, 11, 2),
            profile=profile(),
            evaluations=(evaluation(),),
            market_context="context",
            technical_view="trend",
            bull_case=("support",),
            bear_case=("gap",),
            invalidation_conditions=("breakdown",),
            proposed_direction="short",
            conviction="sell",
            next_check_date=date(2026, 11, 3),
            status="draft",
        )
