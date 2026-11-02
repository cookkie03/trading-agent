from decimal import Decimal

import pytest

from execution.risk import PositionSizing, calculate_position_size


def test_position_size_uses_risk_budget_and_atr_stop_distance():
    sizing = calculate_position_size(
        equity=Decimal("10000"),
        risk_fraction=Decimal("0.005"),
        conviction_multiplier=Decimal("1"),
        atr=Decimal("2"),
        stop_atr_multiple=Decimal("2"),
        entry_price=Decimal("100"),
        max_symbol_fraction=Decimal("0.20"),
    )

    assert sizing == PositionSizing(
        quantity=Decimal("12.5"),
        stop_price=Decimal("96"),
        risk_budget=Decimal("50"),
        notional=Decimal("1250"),
    )


def test_position_size_caps_notional_before_rounding():
    sizing = calculate_position_size(
        equity=Decimal("10000"),
        risk_fraction=Decimal("0.01"),
        conviction_multiplier=Decimal("1"),
        atr=Decimal("2"),
        stop_atr_multiple=Decimal("2"),
        entry_price=Decimal("100"),
        max_symbol_fraction=Decimal("0.05"),
    )

    assert sizing.quantity == Decimal("5")
    assert sizing.notional == Decimal("500")


def test_position_size_rejects_non_positive_inputs():
    with pytest.raises(ValueError, match="atr"):
        calculate_position_size(
            equity=Decimal("10000"),
            risk_fraction=Decimal("0.005"),
            conviction_multiplier=Decimal("1"),
            atr=Decimal("0"),
            stop_atr_multiple=Decimal("2"),
            entry_price=Decimal("100"),
            max_symbol_fraction=Decimal("0.10"),
        )
