from dataclasses import replace
from decimal import Decimal

from agents.risk import RiskAnalyst
from execution.risk import RiskLimits
from tests.workflows.test_trade_cycle import approved_state, portfolio


def test_risk_analyst_finds_atr_after_other_evaluations():
    state = approved_state()
    other = replace(state.evaluations[0], name="momentum", values={"momentum": Decimal("1")})
    state = replace(state, evaluations=(other, *state.evaluations))

    assert RiskAnalyst(RiskLimits()).review(state, portfolio(), Decimal("100")).approved


def test_risk_analyst_approves_state_when_trade_passes_gate():
    result = RiskAnalyst(RiskLimits()).review(approved_state(), portfolio(), Decimal("100"))

    assert result.approved is True
    assert result.state.status == "approved"
    assert result.state.risk_verdict == "approved"
    assert result.state.risk_rationale


def test_risk_analyst_rejects_state_and_preserves_counter_thesis():
    result = RiskAnalyst(
        RiskLimits(max_symbol_exposure=Decimal("0.01"))
    ).review(approved_state(), portfolio(), Decimal("100"))

    assert result.approved is False
    assert result.state.status == "draft"
    assert result.state.risk_verdict == "rejected"
    assert result.state.risk_rationale
    assert result.state.bear_case[-1] == "Risk gate veto: symbol exposure"
