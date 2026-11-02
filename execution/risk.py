"""Deterministic portfolio risk veto for paper-trading intents."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class TradeIntent:
    """Long-only trade proposal before broker submission."""

    symbol: str
    quantity: Decimal
    entry_price: Decimal
    stop_price: Decimal

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("symbol must not be empty")
        if self.quantity <= 0 or self.entry_price <= 0:
            raise ValueError("quantity and entry_price must be positive")
        if self.stop_price <= 0 or self.stop_price >= self.entry_price:
            raise ValueError("stop_price must be positive and below entry_price")

    @property
    def notional(self) -> Decimal:
        return self.quantity * self.entry_price

    @property
    def risk(self) -> Decimal:
        return self.quantity * (self.entry_price - self.stop_price)


@dataclass(frozen=True)
class PositionSizing:
    """Risk-based long position size derived from ATR and portfolio equity."""

    quantity: Decimal
    stop_price: Decimal
    risk_budget: Decimal
    notional: Decimal


@dataclass(frozen=True)
class PortfolioRisk:
    equity: Decimal
    cash: Decimal
    open_risk: Decimal
    symbol_exposure: Decimal

    def __post_init__(self) -> None:
        if self.equity <= 0:
            raise ValueError("equity must be positive")
        if min(self.cash, self.open_risk, self.symbol_exposure) < 0:
            raise ValueError("portfolio values must not be negative")


@dataclass(frozen=True)
class RiskLimits:
    cash_reserve: Decimal = Decimal("0.10")
    max_portfolio_heat: Decimal = Decimal("0.02")
    max_symbol_exposure: Decimal = Decimal("0.10")

    def __post_init__(self) -> None:
        if not 0 <= self.cash_reserve < 1:
            raise ValueError("cash_reserve must be between 0 and 1")
        if min(self.max_portfolio_heat, self.max_symbol_exposure) <= 0:
            raise ValueError("risk limits must be positive")


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    quantity: Decimal
    reasons: tuple[str, ...]


def calculate_position_size(
    *,
    equity: Decimal,
    risk_fraction: Decimal,
    conviction_multiplier: Decimal,
    atr: Decimal,
    stop_atr_multiple: Decimal,
    entry_price: Decimal,
    max_symbol_fraction: Decimal,
) -> PositionSizing:
    """Calculate a capped long-only quantity from a fixed-fractional risk budget."""
    values = {
        "equity": equity,
        "risk_fraction": risk_fraction,
        "conviction_multiplier": conviction_multiplier,
        "atr": atr,
        "stop_atr_multiple": stop_atr_multiple,
        "entry_price": entry_price,
        "max_symbol_fraction": max_symbol_fraction,
    }
    if any(value <= 0 for value in values.values()):
        invalid = next(name for name, value in values.items() if value <= 0)
        raise ValueError(f"{invalid} must be positive")
    risk_budget = equity * risk_fraction * conviction_multiplier
    stop_distance = atr * stop_atr_multiple
    risk_quantity = risk_budget / stop_distance
    capped_notional = min(risk_quantity * entry_price, equity * max_symbol_fraction)
    quantity = capped_notional / entry_price
    return PositionSizing(
        quantity=quantity,
        stop_price=entry_price - stop_distance,
        risk_budget=risk_budget,
        notional=capped_notional,
    )


def evaluate_trade(
    intent: TradeIntent,
    portfolio: PortfolioRisk,
    limits: RiskLimits,
) -> RiskDecision:
    """Approve only if every deterministic portfolio guard passes."""
    reasons: list[str] = []
    available_cash = portfolio.cash - portfolio.equity * limits.cash_reserve
    if intent.notional > available_cash:
        reasons.append("cash")
    if portfolio.symbol_exposure + intent.notional > portfolio.equity * limits.max_symbol_exposure:
        reasons.append("symbol exposure")
    if portfolio.open_risk + intent.risk > portfolio.equity * limits.max_portfolio_heat:
        reasons.append("portfolio heat")
    return RiskDecision(approved=not reasons, quantity=intent.quantity, reasons=tuple(reasons))
