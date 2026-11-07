"""Fail-closed deterministic risk adapter for the research graph; no execution."""

from collections.abc import Mapping
from decimal import Decimal, DecimalException
from typing import Any

from execution.risk import PortfolioRisk, RiskLimits, TradeIntent, evaluate_trade


def _decimal(value: Any) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError("expected a numeric value")
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError("expected a finite value")
    return result


def _intent(proposal: Mapping[str, Any]) -> TradeIntent:
    if proposal["direction"] != "long":
        raise ValueError("only explicit long proposals are supported")
    symbol = proposal["symbol"]
    if not isinstance(symbol, str):
        raise ValueError("symbol must be a string")
    return TradeIntent(
        symbol=symbol,
        **{field: _decimal(proposal[field]) for field in ("quantity", "entry_price", "stop_price")},
    )


def proposal_complete(proposal: dict[str, Any]) -> bool:
    try:
        _intent(proposal)
        return True
    except (KeyError, TypeError, ValueError, DecimalException):
        return False


def risk_gate(context: dict[str, Any]) -> bool:
    try:
        intent = _intent(context["proposal"])
        if not isinstance(context["symbol"], str) or context["symbol"] != intent.symbol:
            return False
        portfolio = PortfolioRisk(
            **{
                field: _decimal(context["portfolio"][field])
                for field in ("equity", "cash", "open_risk", "symbol_exposure")
            }
        )
        return evaluate_trade(intent, portfolio, RiskLimits()).approved is True
    except (KeyError, TypeError, ValueError, DecimalException):
        return False
