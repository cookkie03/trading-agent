from datetime import UTC, datetime
from decimal import Decimal

import pytest

from analysis.strategy_state import (
    MarketContext,
    RiskPlan,
    Signal,
    StrategyDefinition,
    StrategyState,
)

AS_OF = datetime(2026, 11, 1, 15, 30, tzinfo=UTC)


def test_strategy_state_keeps_strategy_specific_parameters_outside_state_shape():
    definition = StrategyDefinition(
        key="trend-following-hourly",
        version="0.1",
        family="trend_following",
        timeframe="1h",
        direction_mode="long_only",
        parameters={"fast_window": 20, "slow_window": 50, "volume_confirmation": True},
    )
    state = StrategyState(
        run_id="run-1",
        symbol="AAPL",
        as_of=AS_OF,
        strategy=definition,
        market=MarketContext(
            price=Decimal("210.00"),
            source_watermark="alpaca:iex:2026-11-01",
            features={"sma_20": Decimal("208.00"), "sma_50": Decimal("201.00")},
        ),
        signal=Signal(direction="long", score=Decimal("0.75"), rationale="trend confirmed"),
        risk=RiskPlan(stop_loss=Decimal("200.00"), quantity=Decimal("2")),
    )

    assert state.strategy.parameters["fast_window"] == 20
    assert state.signal.direction == "long"
    assert state.is_ready_for_trade() is True


def test_flat_signal_does_not_require_position_risk():
    state = StrategyState(
        run_id="run-2",
        symbol="AAPL",
        as_of=AS_OF,
        strategy=StrategyDefinition(
            key="mean-reversion",
            version="0.1",
            family="mean_reversion",
            timeframe="1h",
            direction_mode="long_short",
            parameters={"lookback": 20},
        ),
        market=MarketContext(
            price=Decimal("210.00"),
            source_watermark="alpaca:iex:2026-11-01",
            features={"z_score": Decimal("0.1")},
        ),
        signal=Signal(direction="flat", score=Decimal("0"), rationale="no edge"),
    )

    assert state.is_ready_for_trade() is True


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (lambda: MarketContext(Decimal("0"), "watermark", {}), "price must be positive"),
        (
            lambda: StrategyDefinition("x", "0.1", "trend_following", "1d", "long_only", {}),
            "parameters must not be empty",
        ),
        (
            lambda: Signal("long", Decimal("1.1"), "reason"),
            "score must be between -1 and 1",
        ),
    ],
)
def test_strategy_state_parts_reject_invalid_values(factory, message):
    with pytest.raises(ValueError, match=message):
        factory()


def test_short_signal_is_rejected_by_long_only_strategy():
    with pytest.raises(ValueError, match="does not allow short signals"):
        StrategyState(
            run_id="run-3",
            symbol="AAPL",
            as_of=AS_OF,
            strategy=StrategyDefinition(
                key="trend-following-hourly",
                version="0.1",
                family="trend_following",
                timeframe="1h",
                direction_mode="long_only",
                parameters={"window": 20},
            ),
            market=MarketContext(Decimal("210"), "watermark", {}),
            signal=Signal("short", Decimal("-0.5"), "trend failed"),
            risk=RiskPlan(stop_loss=Decimal("220"), quantity=Decimal("1")),
        )
