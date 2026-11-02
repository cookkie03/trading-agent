from decimal import Decimal

import pytest

from agents.desks import DeskOpinion
from tests.workflows.test_trade_cycle import approved_state
from workflows.langgraph_workflow import build_research_graph


@pytest.mark.parametrize("change", ["unknown", "duplicate", "identity", "missing"])
def test_pm_invalid_review_never_approves(monkeypatch, change):
    opinions = tuple(
        DeskOpinion(name, "view", "reason", (name,))
        for name in ("market", "technical", "fundamentals", "sentiment")
    )
    monkeypatch.setattr("workflows.langgraph_workflow.run_desks", lambda context: opinions)

    def reviewer(research, desks):
        review = {
            "run_id": research.run_id,
            "symbol": research.symbol,
            "decision": "approve",
            "thesis": "trend",
            "counter_thesis": "reversal",
            "uncertainties": "earnings",
            "evidence": [o.evidence[0] for o in desks],
        }
        if change == "unknown":
            review["evidence"].append("invented")
        elif change == "duplicate":
            review["evidence"].append("market")
        elif change == "identity":
            review["symbol"] = "OTHER"
        else:
            review["evidence"].pop()
        return review

    result = build_research_graph(pm_reviewer=reviewer).invoke(
        {
            "research": approved_state(),
            "portfolio": {
                "equity": Decimal("10000"),
                "cash": Decimal("5000"),
                "open_risk": Decimal("0"),
                "symbol_exposure": Decimal("0"),
            },
            "limits": {"max_symbol_exposure": Decimal("0.10")},
            "entry_price": Decimal("100"),
        }
    )
    assert result["decision"] == "pending"
