"""Deterministic composition of approved research, risk and paper execution."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from analysis.strategy_state import ResearchState
from execution.paper import IdempotentPaperExecutor, OrderRequest, Submission
from execution.risk import (
    PortfolioRisk,
    RiskDecision,
    RiskLimits,
    TradeIntent,
    calculate_position_size,
    evaluate_trade,
)


@dataclass(frozen=True)
class TradeCycleResult:
    risk: RiskDecision
    submission: Submission | None


class TradeCycle:
    """Keep orchestration thin while preserving deep domain seams."""

    def __init__(self, executor: IdempotentPaperExecutor) -> None:
        self._executor = executor

    def run(
        self,
        state: ResearchState,
        portfolio: PortfolioRisk,
        limits: RiskLimits,
        entry_price: Decimal,
    ) -> TradeCycleResult:
        investment = state.to_investment_state()
        evaluation = investment.research.evaluations[0]
        atr = evaluation.values.get("atr")
        if atr is None:
            raise ValueError("approved state must include atr evaluation")
        sizing = calculate_position_size(
            equity=portfolio.equity,
            risk_fraction=Decimal("0.005"),
            conviction_multiplier=Decimal("1"),
            atr=atr,
            stop_atr_multiple=Decimal("2"),
            entry_price=entry_price,
            max_symbol_fraction=Decimal("0.10"),
        )
        request = OrderRequest(
            client_order_id=f"{state.run_id}:{state.symbol}",
            symbol=state.symbol,
            quantity=sizing.quantity,
            limit_price=entry_price,
            stop_price=sizing.stop_price,
        )
        risk = evaluate_trade(request_to_intent(request), portfolio, limits)
        if not risk.approved:
            return TradeCycleResult(risk=risk, submission=None)
        return TradeCycleResult(
            risk=risk,
            submission=self._executor.submit(request, risk),
        )


def request_to_intent(request: OrderRequest) -> TradeIntent:
    return TradeIntent(
        symbol=request.symbol,
        quantity=request.quantity,
        entry_price=request.limit_price,
        stop_price=request.stop_price,
    )
