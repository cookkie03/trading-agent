from decimal import Decimal

from execution.paper import IdempotentPaperExecutor
from execution.risk import RiskLimits
from storage.sqlite import SQLiteDatabase
from tests.workflows.test_trade_cycle import Gateway, approved_state, portfolio
from workflows.trade_cycle import TradeCycle, TradeCycleResult


def test_trade_cycle_persists_approved_decision(tmp_path):
    database = SQLiteDatabase(tmp_path / "cycle.db")
    cycle = TradeCycle(IdempotentPaperExecutor(Gateway()), database.decisions)

    result = cycle.run(approved_state(), portfolio(), RiskLimits(), Decimal("100"))

    assert isinstance(result, TradeCycleResult)
    assert database.decisions.latest()[0].status == "risk_approved"
    database.close()


def test_trade_cycle_persists_veto_decision(tmp_path):
    database = SQLiteDatabase(tmp_path / "cycle.db")
    cycle = TradeCycle(
        IdempotentPaperExecutor(Gateway()),
        database.decisions,
    )

    result = cycle.run(
        approved_state(),
        portfolio(),
        RiskLimits(max_symbol_exposure=Decimal("0.01")),
        Decimal("100"),
    )

    assert result.submission is None
    assert database.decisions.latest()[0].status == "risk_rejected"
    database.close()
