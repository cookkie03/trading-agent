from datetime import UTC, date, datetime
from decimal import Decimal

from agents.research import ResearchInputs, build_research_state
from analysis.strategy_state import QuantitativeEvaluation, StrategyProfile


def test_research_builder_creates_draft_with_explicit_desk_contribution():
    profile = StrategyProfile(
        key="trend-following-hourly",
        version="0.1",
        objective="Find liquid US equity trends",
        family="trend_following",
        timeframe="1h",
        direction_mode="long_only",
        questions=("Is trend persistent?",),
        tools=("technical_indicators",),
        expected_evidence=("hourly OHLCV",),
        constraints=("US equities", "USD", "paper only"),
    )
    evaluation = QuantitativeEvaluation(
        name="ema_alignment",
        values={"fast_ema": Decimal("105"), "slow_ema": Decimal("100")},
        observed_at=datetime(2026, 11, 2, 14, tzinfo=UTC),
        source="sqlite:price_bars",
        parameters={"fast_window": 20, "slow_window": 50},
        formula_version="ema-v1",
        interpretation="fast EMA is above slow EMA",
    )

    state = build_research_state(
        ResearchInputs(
            run_id="run-1",
            symbol="AAPL",
            as_of=date(2026, 11, 2),
            profile=profile,
            evaluations=(evaluation,),
            market_context="regular US session",
            technical_view="positive trend",
            bull_case=("EMA alignment",),
            bear_case=("earnings gap",),
            invalidation_conditions=("close below slow EMA",),
            proposed_direction="long",
            conviction="buy",
            next_check_date=date(2026, 11, 3),
        )
    )

    assert state.status == "draft"
    assert state.risk_verdict is None
    assert state.technical_view == "positive trend"
    assert state.evaluations[0].source == "sqlite:price_bars"
