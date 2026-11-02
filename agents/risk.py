"""Risk analyst seam: critique the thesis, then apply deterministic vetoes."""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal

from analysis.strategy_state import ResearchState
from execution.risk import PortfolioRisk, RiskDecision, RiskLimits, TradeIntent, evaluate_trade


@dataclass(frozen=True)
class RiskReview:
    approved: bool
    state: ResearchState
    decision: RiskDecision


class RiskAnalyst:
    def __init__(self, limits: RiskLimits) -> None:
        self._limits = limits

    def review(
        self,
        state: ResearchState,
        portfolio: PortfolioRisk,
        entry_price: Decimal,
    ) -> RiskReview:
        evaluation = state.evaluations[0]
        atr = evaluation.values.get("atr")
        if atr is None:
            raise ValueError("risk review requires atr evaluation")
        intent = TradeIntent(
            symbol=state.symbol,
            quantity=Decimal("10"),
            entry_price=entry_price,
            stop_price=entry_price - (atr * Decimal("2")),
        )
        decision = evaluate_trade(intent, portfolio, self._limits)
        if decision.approved:
            reviewed = replace(
                state,
                status="approved",
                risk_verdict="approved",
                risk_rationale="Risk gate passed; counter-thesis remains recorded.",
            )
        else:
            reason = "; ".join(decision.reasons)
            reviewed = replace(
                state,
                status="draft",
                risk_verdict="rejected",
                risk_rationale=f"Risk gate veto: {reason}",
                bear_case=(*state.bear_case, f"Risk gate veto: {reason}"),
            )
        return RiskReview(approved=decision.approved, state=reviewed, decision=decision)
