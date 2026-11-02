"""Deterministic composition of approved research, risk and paper execution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
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
from storage.sqlite import DecisionRecord


@dataclass(frozen=True)
class TradeCycleResult:
    risk: RiskDecision
    submission: Submission | None


class TradeCycle:
    """Keep orchestration thin while preserving deep domain seams."""

    def __init__(self, executor: IdempotentPaperExecutor, decisions=None) -> None:
        self._executor = executor
        self._decisions = decisions

    def run(
        self,
        state: ResearchState,
        portfolio: PortfolioRisk,
        limits: RiskLimits,
        entry_price: Decimal,
    ) -> TradeCycleResult:
        investment = state.to_investment_state()
        if investment.research.proposed_direction != "long":
            raise ValueError("paper trade cycle requires a long direction")
        atr = next(
            (evaluation.values["atr"] for evaluation in investment.research.evaluations
             if "atr" in evaluation.values),
            None,
        )
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
            take_profit_price=entry_price + (atr * Decimal("3")),
            stop_price=sizing.stop_price,
        )
        risk = evaluate_trade(request_to_intent(request), portfolio, limits)
        if not risk.approved:
            self._save_decision(state, risk, None)
            return TradeCycleResult(risk=risk, submission=None)
        submission = self._executor.submit(request, risk)
        self._save_decision(state, risk, submission)
        return TradeCycleResult(risk=risk, submission=submission)

    def _save_decision(self, state, risk: RiskDecision, submission: Submission | None) -> None:
        if self._decisions is None:
            return
        self._decisions.save(
            DecisionRecord(
                client_order_id=f"{state.run_id}:{state.symbol}",
                symbol=state.symbol,
                status="risk_approved" if risk.approved else "risk_rejected",
                direction=state.proposed_direction,
                conviction=state.conviction,
                rationale=(
                    "paper order submitted"
                    if submission is not None
                    else "; ".join(risk.reasons)
                ),
                observed_at=datetime.now(UTC),
                payload=state.run_id,
            )
        )


def request_to_intent(request: OrderRequest) -> TradeIntent:
    return TradeIntent(
        symbol=request.symbol,
        quantity=request.quantity,
        entry_price=request.limit_price,
        stop_price=request.stop_price,
    )
