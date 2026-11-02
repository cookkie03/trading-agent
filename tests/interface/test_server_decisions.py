import json
from datetime import UTC, datetime
from urllib.request import Request, urlopen

from interface.dashboard import SQLiteDashboardReadModel
from interface.server import DashboardServer
from storage.sqlite import DecisionRecord, SQLiteDatabase


def test_provider_data_reaches_dashboard_before_pending_research(tmp_path):
    from decimal import Decimal

    from data.ingestion import ingest_ohlcv
    from execution.risk import RiskLimits
    from tests.data.test_ingestion import FakeProvider, make_bar
    from tests.workflows.test_trade_cycle import approved_state, portfolio
    from workflows.paper_runtime import run_research_cycle

    path = tmp_path / "provider.db"
    with SQLiteDatabase(path) as database:
        ingest_ohlcv(
            FakeProvider((make_bar(),)),
            database,
            symbol="AAPL",
            start=datetime(2026, 10, 1, tzinfo=UTC),
            end=datetime(2026, 11, 1, tzinfo=UTC),
        )
        result = run_research_cycle(
            None, database, approved_state(), portfolio(), RiskLimits(), Decimal("104")
        )
        assert result["decision"] == "pending"
    server = DashboardServer(SQLiteDashboardReadModel(path), port=0)
    server.start()
    try:
        with urlopen(server.url("/api/dashboard")) as response:
            payload = json.load(response)
    finally:
        server.close()
    assert payload["watchlist"][0]["symbol"] == "AAPL"
    assert payload["decisions"][0]["status"] == "pending"


def test_missing_desk_evidence_does_not_produce_an_approved_decision_over_http(tmp_path):
    from decimal import Decimal

    from tests.workflows.test_trade_cycle import approved_state
    from workflows.langgraph_workflow import build_research_graph

    result = build_research_graph().invoke(
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
    path = tmp_path / "incomplete.db"
    with SQLiteDatabase(path) as database:
        database.decisions.save(
            DecisionRecord(
                client_order_id="run-1:AAPL",
                symbol="AAPL",
                status=result["decision"],
                direction="long",
                conviction="buy",
                rationale="desk evidence pending",
                observed_at=datetime.now(UTC),
                payload="run-1",
            )
        )
    server = DashboardServer(SQLiteDashboardReadModel(path), port=0)
    server.start()
    try:
        with urlopen(server.url("/api/dashboard")) as response:
            decision = json.load(response)["decisions"][0]
    finally:
        server.close()
    assert decision["status"] != "approved"


def test_reviewed_trade_uses_same_risk_quantity_through_dashboard(tmp_path):
    from dataclasses import replace
    from decimal import Decimal

    from agents.risk import RiskAnalyst
    from execution.paper import IdempotentPaperExecutor
    from execution.risk import RiskLimits
    from tests.workflows.test_trade_cycle import Gateway, approved_state, portfolio
    from workflows.trade_cycle import TradeCycle

    state = approved_state()
    state = replace(
        state, evaluations=(replace(state.evaluations[0], values={"atr": Decimal("4")}),)
    )
    # Ten shares fail this limit, but the ATR-sized 6.25 shares pass.
    limits = RiskLimits(max_symbol_exposure=Decimal("0.08"))
    review = RiskAnalyst(limits).review(state, portfolio(), Decimal("100"))
    assert review.approved

    path = tmp_path / "review.db"
    with SQLiteDatabase(path) as database:
        cycle = TradeCycle(
            IdempotentPaperExecutor(Gateway(), database.paper_orders), database.decisions
        )
        result = cycle.run(review.state, portfolio(), limits, Decimal("100"))
        assert result.submission is not None
    server = DashboardServer(SQLiteDashboardReadModel(path), port=0)
    server.start()
    try:
        with urlopen(server.url("/api/dashboard")) as response:
            decision = json.load(response)["decisions"][0]
    finally:
        server.close()
    assert decision["status"] == "risk_approved"


def test_trade_cycle_decision_survives_restart_and_is_visible_over_http(tmp_path):
    from decimal import Decimal

    from execution.paper import IdempotentPaperExecutor
    from execution.risk import RiskLimits
    from tests.workflows.test_trade_cycle import Gateway, approved_state, portfolio
    from workflows.trade_cycle import TradeCycle

    path = tmp_path / "cycle.db"
    with SQLiteDatabase(path) as database:
        executor = IdempotentPaperExecutor(Gateway(), database.paper_orders)
        result = TradeCycle(executor, database.decisions).run(
            approved_state(), portfolio(), RiskLimits(), Decimal("100")
        )
        assert result.submission.broker_order_id == "paper-1"
    server = DashboardServer(SQLiteDashboardReadModel(path), port=0)
    server.start()
    try:
        with urlopen(server.url("/api/dashboard")) as response:
            decision = json.load(response)["decisions"][0]
    finally:
        server.close()
    assert decision["symbol"] == "AAPL"
    assert decision["status"] == "risk_approved"
    assert decision["direction"] == "long"
    assert decision["conviction"] == "buy"
    assert decision["rationale"] == "paper order submitted"


def test_http_dashboard_exposes_persisted_decision_queue(tmp_path):
    database = SQLiteDatabase(tmp_path / "server.db")
    database.decisions.save(
        DecisionRecord(
            client_order_id="run-1:AAPL",
            symbol="AAPL",
            status="risk_approved",
            direction="long",
            conviction="buy",
            rationale="trend confirmed",
            observed_at=datetime(2026, 11, 2, 15, tzinfo=UTC),
            payload="run-1",
        )
    )
    database.close()
    server = DashboardServer(SQLiteDashboardReadModel(tmp_path / "server.db"), port=0)
    server.start()

    try:
        with urlopen(Request(server.url("/api/dashboard"), method="GET")) as response:
            payload = json.load(response)
    finally:
        server.close()

    assert payload["decisions"][0]["symbol"] == "AAPL"
    assert payload["modules"]["decisions"] == "available"
