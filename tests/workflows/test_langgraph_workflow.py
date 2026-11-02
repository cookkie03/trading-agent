from decimal import Decimal

from tests.workflows.test_trade_cycle import approved_state
from workflows.langgraph_workflow import build_research_graph


def test_research_graph_compiles_and_runs_deterministic_review():
    graph = build_research_graph()
    state = approved_state()

    result = graph.invoke(
        {
            "research": state,
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

    assert result["risk_review"].approved is True
