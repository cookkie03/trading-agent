from decimal import Decimal

import pytest

from execution.risk import PortfolioRisk, RiskLimits, TradeIntent, evaluate_trade


def intent(quantity="10", entry="100", stop="95"):
    return TradeIntent(
        symbol="AAPL",
        quantity=Decimal(quantity),
        entry_price=Decimal(entry),
        stop_price=Decimal(stop),
    )


def portfolio(**overrides):
    values = {
        "equity": Decimal("10000"),
        "cash": Decimal("5000"),
        "open_risk": Decimal("100"),
        "symbol_exposure": Decimal("0"),
    }
    values.update(overrides)
    return PortfolioRisk(**values)


def test_risk_gate_approves_trade_within_cash_exposure_and_heat_limits():
    result = evaluate_trade(intent(), portfolio(), RiskLimits())

    assert result.approved is True
    assert result.quantity == Decimal("10")
    assert result.reasons == ()


def test_risk_gate_vetoes_long_only_trade_that_exceeds_cash():
    result = evaluate_trade(intent(quantity="60"), portfolio(), RiskLimits())

    assert result.approved is False
    assert "cash" in result.reasons


def test_risk_gate_vetoes_trade_that_exceeds_portfolio_heat():
    result = evaluate_trade(
        intent(quantity="100"),
        portfolio(),
        RiskLimits(max_portfolio_heat=Decimal("0.05")),
    )

    assert result.approved is False
    assert "portfolio heat" in result.reasons


def test_risk_gate_rejects_invalid_stop_for_long_trade():
    with pytest.raises(ValueError, match="stop_price"):
        intent(stop="105")
