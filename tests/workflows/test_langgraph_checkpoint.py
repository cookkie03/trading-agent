from decimal import Decimal

from langgraph.checkpoint.memory import MemorySaver

from tests.workflows.test_trade_cycle import approved_state
from workflows.langgraph_workflow import build_research_graph


def test_graph_accepts_checkpoint_saver_and_keeps_thread_state():
    graph = build_research_graph(checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "run-1"}}

    result = graph.invoke(
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
        },
        config,
    )

    assert result["decision"] == "pending"
    checkpoint = graph.get_state(config)
    assert checkpoint.values["decision"] == "pending"
