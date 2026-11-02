from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from analysis.strategy_state import QuantitativeEvaluation, ResearchState, StrategyProfile
from execution.paper import IdempotentPaperExecutor, Submission
from execution.risk import PortfolioRisk, RiskLimits
from workflows.trade_cycle import TradeCycle, TradeCycleResult


class Gateway:
    def submit(self, request):
        return Submission(request.client_order_id, "paper-1")


def approved_state() -> ResearchState:
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
        name="atr",
        values={"atr": Decimal("2")},
        observed_at=datetime(2026, 11, 2, 14, tzinfo=UTC),
        source="sqlite:price_bars",
        parameters={"window": 14},
        formula_version="atr-wilder-v1",
        interpretation="normal volatility",
    )
    return ResearchState(
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
        status="approved",
        risk_verdict="approved",
        risk_rationale="within limits",
    )


def test_trade_cycle_does_not_buy_when_research_is_flat():
    cycle = TradeCycle(IdempotentPaperExecutor(Gateway()))
    state = replace(approved_state(), proposed_direction="flat")

    with pytest.raises(ValueError, match="long"):
        cycle.run(state, portfolio(), RiskLimits(), Decimal("100"))


def portfolio() -> PortfolioRisk:
    return PortfolioRisk(
        equity=Decimal("10000"),
        cash=Decimal("5000"),
        open_risk=Decimal("0"),
        symbol_exposure=Decimal("0"),
    )


def test_trade_cycle_submits_only_after_state_and_risk_approval():
    executor = IdempotentPaperExecutor(Gateway())
    cycle = TradeCycle(executor)

    result = cycle.run(approved_state(), portfolio(), RiskLimits(), Decimal("100"))

    assert isinstance(result, TradeCycleResult)
    assert result.submission == Submission("run-1:AAPL", "paper-1")
    assert result.risk.approved is True


def test_trade_cycle_returns_veto_without_submitting():
    executor = IdempotentPaperExecutor(Gateway())
    cycle = TradeCycle(executor)
    limits = RiskLimits(max_symbol_exposure=Decimal("0.01"))

    result = cycle.run(approved_state(), portfolio(), limits, Decimal("100"))

    assert result.submission is None
    assert result.risk.approved is False
    assert result.risk.reasons == ("symbol exposure",)
