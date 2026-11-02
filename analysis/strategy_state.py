"""Generic strategy state used by deterministic signal and risk modules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

Direction = Literal["long", "short", "flat"]
DirectionMode = Literal["long_only", "long_short", "short_only"]
Conviction = Literal["strong_buy", "buy", "hold", "sell", "strong_sell"]
ResearchStatus = Literal["draft", "approved"]


@dataclass(frozen=True)
class StrategyProfile:
    """Stable strategy brief consumed by research desks."""

    key: str
    version: str
    objective: str
    family: str
    timeframe: str
    direction_mode: DirectionMode
    questions: tuple[str, ...]
    tools: tuple[str, ...]
    expected_evidence: tuple[str, ...]
    constraints: tuple[str, ...]

    def __post_init__(self) -> None:
        fields = (self.key, self.version, self.objective, self.family, self.timeframe)
        if any(not field.strip() for field in fields):
            raise ValueError("strategy profile identity fields must not be empty")
        if not all((self.questions, self.tools, self.expected_evidence, self.constraints)):
            raise ValueError("strategy profile requirements must not be empty")


@dataclass(frozen=True)
class QuantitativeEvaluation:
    """A versioned numeric observation with enough provenance to reproduce it."""

    name: str
    values: dict[str, Decimal]
    observed_at: datetime
    source: str
    parameters: dict[str, Any]
    formula_version: str
    interpretation: str

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.source.strip() or not self.formula_version.strip():
            raise ValueError("quantitative evaluation identity fields must not be empty")
        if not self.values or not self.parameters or not self.interpretation.strip():
            raise ValueError(
                "quantitative evaluation must include values, parameters and interpretation"
            )


@dataclass(frozen=True)
class ResearchState:
    """Research thesis at draft or risk-approved maturity."""

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
    status: ResearchStatus
    risk_verdict: str | None = None
    risk_rationale: str | None = None

    def __post_init__(self) -> None:
        if not self.run_id.strip() or not self.symbol.strip():
            raise ValueError("run_id and symbol must not be empty")
        if not self.evaluations:
            raise ValueError("research state requires quantitative evaluations")
        if self.proposed_direction == "short" and self.profile.direction_mode == "long_only":
            raise ValueError("short direction is incompatible with long_only profile")
        required_text = (
            self.market_context,
            self.technical_view,
            *self.bull_case,
            *self.bear_case,
            *self.invalidation_conditions,
        )
        if any(not text.strip() for text in required_text):
            raise ValueError("research state text fields must not be empty")
        if self.next_check_date < self.as_of:
            raise ValueError("next_check_date must not precede as_of")

    def is_complete(self) -> bool:
        return bool(self.bull_case and self.bear_case and self.invalidation_conditions)

    def can_be_approved(self) -> bool:
        return self.is_complete() and self.status == "approved" and self.risk_verdict == "approved"

    def to_investment_state(self) -> InvestmentState:
        if not self.can_be_approved():
            raise ValueError("research state is not risk-approved")
        return InvestmentState(research=self)


@dataclass(frozen=True)
class InvestmentState:
    """Validated research state that is eligible for deterministic execution."""

    research: ResearchState
    status: Literal["approved"] = "approved"


@dataclass(frozen=True)
class StrategyDefinition:
    key: str
    version: str
    family: str
    timeframe: str
    direction_mode: DirectionMode
    parameters: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.key.strip() or not self.version.strip() or not self.family.strip():
            raise ValueError("strategy identity fields must not be empty")
        if not self.parameters:
            raise ValueError("parameters must not be empty")


@dataclass(frozen=True)
class MarketContext:
    price: Decimal
    source_watermark: str
    features: dict[str, Decimal]

    def __post_init__(self) -> None:
        if self.price <= 0:
            raise ValueError("price must be positive")
        if not self.source_watermark.strip():
            raise ValueError("source_watermark must not be empty")


@dataclass(frozen=True)
class Signal:
    direction: Direction
    score: Decimal
    rationale: str

    def __post_init__(self) -> None:
        if not -1 <= self.score <= 1:
            raise ValueError("score must be between -1 and 1")
        if not self.rationale.strip():
            raise ValueError("rationale must not be empty")


@dataclass(frozen=True)
class RiskPlan:
    stop_loss: Decimal
    quantity: Decimal

    def __post_init__(self) -> None:
        if self.stop_loss <= 0:
            raise ValueError("stop_loss must be positive")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")


@dataclass(frozen=True)
class StrategyState:
    run_id: str
    symbol: str
    as_of: datetime
    strategy: StrategyDefinition
    market: MarketContext
    signal: Signal
    risk: RiskPlan | None = None

    def __post_init__(self) -> None:
        if not self.run_id.strip() or not self.symbol.strip():
            raise ValueError("run_id and symbol must not be empty")
        if self.signal.direction == "short" and self.strategy.direction_mode == "long_only":
            raise ValueError("strategy does not allow short signals")
        if self.signal.direction == "long" and self.strategy.direction_mode == "short_only":
            raise ValueError("strategy does not allow long signals")

    def is_ready_for_trade(self) -> bool:
        return self.signal.direction == "flat" or self.risk is not None
