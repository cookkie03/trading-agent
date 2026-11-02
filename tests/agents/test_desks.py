from datetime import date
from decimal import Decimal

from agents.desks import DeskContext, run_desks
from tests.workflows.test_trade_cycle import approved_state


def test_all_required_desks_return_named_contributions():
    state = approved_state()
    opinions = run_desks(
        DeskContext(
            symbol=state.symbol,
            as_of=date(2026, 11, 2),
            current_price=Decimal("100"),
            research=state,
        )
    )

    assert {opinion.desk for opinion in opinions} == {
        "market",
        "technical",
        "fundamentals",
        "sentiment",
    }
    assert all(opinion.view and opinion.rationale for opinion in opinions)
    assert opinions[1].evidence == (
        "atr | sqlite:price_bars | atr-wilder-v1 | 2026-11-02T14:00:00+00:00",
    )
