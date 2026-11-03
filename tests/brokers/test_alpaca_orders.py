from decimal import Decimal
from types import SimpleNamespace

from brokers.alpaca_orders import AlpacaPaperOrders, PaperOrderRequest
from execution.paper import IdempotentPaperExecutor, OrderRequest
from execution.risk import RiskDecision, RiskLimits
from tests.workflows.test_trade_cycle import approved_state, portfolio
from workflows.trade_cycle import TradeCycle


class FakeClient:
    def __init__(self):
        self.submitted = []
        self.cancelled = []

    def submit_order(self, request):
        self.submitted.append(request)
        return SimpleNamespace(id="broker-1", client_order_id=request.client_order_id)

    def cancel_order_by_id(self, order_id):
        self.cancelled.append(order_id)


def test_lookup_normalizes_cancelled_broker_status():
    class LookupClient(FakeClient):
        def get_order_by_client_id(self, client_order_id):
            return SimpleNamespace(
                id="broker-1", client_order_id=client_order_id, status="canceled"
            )

    result = AlpacaPaperOrders(LookupClient()).find_by_client_order_id("run-1:AAPL")
    assert result.status == "CANCELLED"


def test_paper_orders_submit_and_cancel_through_injected_client():
    client = FakeClient()
    adapter = AlpacaPaperOrders(client)
    request = PaperOrderRequest(
        client_order_id="run-1:AAPL",
        symbol="AAPL",
        quantity=Decimal("10"),
        limit_price=Decimal("100"),
        take_profit_price=Decimal("110"),
        stop_price=Decimal("95"),
    )

    submitted = adapter.submit(request)
    adapter.cancel(submitted.broker_order_id)

    assert submitted.broker_order_id == "broker-1"
    assert client.submitted[0].take_profit.limit_price == 110.0
    assert client.cancelled == ["broker-1"]


def test_trade_cycle_submits_approved_paper_bracket_to_alpaca():
    client = FakeClient()
    cycle = TradeCycle(IdempotentPaperExecutor(AlpacaPaperOrders(client)))

    result = cycle.run(approved_state(), portfolio(), RiskLimits(), Decimal("100"))

    assert result.submission.broker_order_id == "broker-1"
    assert client.submitted[0].client_order_id == "run-1:AAPL"
    assert client.submitted[0].take_profit.limit_price == 106.0
    assert client.submitted[0].stop_loss.stop_price == 96.0


def test_paper_runtime_rejects_live_endpoint_before_client_creation(tmp_path):
    import pytest

    from config import Settings
    from storage.sqlite import SQLiteDatabase
    from workflows.paper_runtime import alpaca_paper_runtime

    settings = Settings(
        ALPACA_API_KEY="test",
        ALPACA_SECRET_KEY="test",
        ALPACA_TRADING_URL="https://api.alpaca.markets/v2",
    )
    with SQLiteDatabase(tmp_path / "paper.db") as database:
        with pytest.raises(ValueError, match="paper endpoint"):
            alpaca_paper_runtime(settings, database)


def test_research_pipeline_records_pending_without_claiming_missing_evidence(tmp_path):
    from interface.dashboard import SQLiteDashboardReadModel
    from storage.sqlite import SQLiteDatabase
    from workflows.paper_runtime import run_research_cycle

    with SQLiteDatabase(tmp_path / "reason.db") as database:
        result = run_research_cycle(
            FakeClient(), database, approved_state(), portfolio(), RiskLimits(), Decimal("100")
        )
        assert result["decision"] == "pending"
    decisions = SQLiteDashboardReadModel(tmp_path / "reason.db").snapshot().decisions
    assert "PM" in decisions[0].rationale


def test_pm_review_can_authorize_paper_only_with_cited_evidence(tmp_path):
    from dataclasses import replace
    from datetime import UTC, datetime

    from data.providers.alpaca_news import NewsItem
    from data.providers.yahoo_fundamentals import FundamentalObservation
    from storage.sqlite import SQLiteDatabase
    from tests.data.test_ingestion import make_bar
    from workflows.paper_runtime import run_research_cycle

    timestamp = datetime(2026, 11, 2, 14, tzinfo=UTC)
    client = FakeClient()

    def reviewer(research, opinions):
        return {
            "run_id": research.run_id,
            "symbol": research.symbol,
            "decision": "approve",
            "thesis": "Trend persists",
            "counter_thesis": "Earnings could reverse trend",
            "uncertainties": "Limited market context",
            "evidence": [o.evidence[0] for o in opinions],
        }

    with SQLiteDatabase(tmp_path / "review.db") as database:
        result = run_research_cycle(
            client,
            database,
            approved_state(),
            portfolio(),
            RiskLimits(),
            Decimal("100"),
            market_bar=replace(make_bar(), symbol="SPY"),
            news=(NewsItem("Earnings", "wire", "https://example.org/n", timestamp),),
            fundamentals=(
                FundamentalObservation("AAPL", "market_cap", Decimal("100"), "test", timestamp),
            ),
            pm_reviewer=reviewer,
        )
        import json

        records = database.decisions.latest()
        review = next(record for record in records if record.status == "pm_approved")
        assert json.loads(review.payload)["counter_thesis"] == "Earnings could reverse trend"
    with SQLiteDatabase(tmp_path / "review.db") as database:
        retry = run_research_cycle(
            client,
            database,
            approved_state(),
            portfolio(),
            RiskLimits(),
            Decimal("100"),
            market_bar=replace(make_bar(), symbol="SPY"),
            news=(NewsItem("Earnings", "wire", "https://example.org/n", timestamp),),
            fundamentals=(
                FundamentalObservation("AAPL", "market_cap", Decimal("100"), "test", timestamp),
            ),
            pm_reviewer=reviewer,
        )
        assert retry["execution"].submission.broker_order_id == "broker-1"

        def conflicting_review(research, opinions):
            return {**reviewer(research, opinions), "thesis": "Different thesis"}

        import pytest

        with pytest.raises(ValueError, match="conflicting PM review"):
            run_research_cycle(
                client,
                database,
                approved_state(),
                portfolio(),
                RiskLimits(),
                Decimal("100"),
                market_bar=replace(make_bar(), symbol="SPY"),
                news=(NewsItem("Earnings", "wire", "https://example.org/n", timestamp),),
                fundamentals=(
                    FundamentalObservation("AAPL", "market_cap", Decimal("100"), "test", timestamp),
                ),
                pm_reviewer=conflicting_review,
            )
    assert result["decision"] == "approved"
    assert len(client.submitted) == 1


def test_pm_submit_timeout_does_not_resubmit_after_restart(tmp_path):
    from dataclasses import replace
    from datetime import UTC, datetime

    import pytest

    from data.providers.alpaca_news import NewsItem
    from data.providers.yahoo_fundamentals import FundamentalObservation
    from storage.sqlite import SQLiteDatabase
    from tests.data.test_ingestion import make_bar
    from workflows.paper_runtime import run_research_cycle

    class TimeoutClient(FakeClient):
        def submit_order(self, request):
            self.submitted.append(request)
            raise TimeoutError("response lost")

        def get_order_by_client_id(self, client_order_id):
            return SimpleNamespace(
                id="broker-1", client_order_id=client_order_id, status="accepted"
            )

    def reviewer(research, opinions):
        return {
            "run_id": research.run_id,
            "symbol": research.symbol,
            "decision": "approve",
            "thesis": "Trend",
            "counter_thesis": "Reversal",
            "uncertainties": "Earnings",
            "evidence": [opinion.evidence[0] for opinion in opinions],
        }

    timestamp = datetime(2026, 11, 2, 14, tzinfo=UTC)
    client = TimeoutClient()
    path = tmp_path / "timeout.db"
    kwargs = dict(
        market_bar=replace(make_bar(), symbol="SPY"),
        news=(NewsItem("Earnings", "wire", "https://example.org/n", timestamp),),
        fundamentals=(
            FundamentalObservation("AAPL", "market_cap", Decimal("100"), "test", timestamp),
        ),
        pm_reviewer=reviewer,
    )
    with SQLiteDatabase(path) as database:
        with pytest.raises(TimeoutError):
            run_research_cycle(
                client,
                database,
                approved_state(),
                portfolio(),
                RiskLimits(),
                Decimal("100"),
                **kwargs,
            )
    with SQLiteDatabase(path) as database:
        with pytest.raises(RuntimeError):
            run_research_cycle(
                client,
                database,
                approved_state(),
                portfolio(),
                RiskLimits(),
                Decimal("100"),
                **kwargs,
            )
        from workflows.paper_runtime import paper_runtime

        _, executor = paper_runtime(client, database)
        order = OrderRequest(
            "run-1:AAPL", "AAPL", Decimal("10"), Decimal("100"), Decimal("106"), Decimal("96")
        )
        assert executor.reconcile(order).broker_order_id == "broker-1"
        resumed = run_research_cycle(
            client, database, approved_state(), portfolio(), RiskLimits(), Decimal("100"), **kwargs
        )
        assert resumed["execution"].submission.broker_order_id == "broker-1"
    assert len(client.submitted) == 1


def test_pm_rejection_is_recorded_without_submitting(tmp_path):
    from storage.sqlite import SQLiteDatabase
    from workflows.paper_runtime import run_research_cycle

    client = FakeClient()

    def reviewer(research, opinions):
        return {
            "run_id": research.run_id,
            "symbol": research.symbol,
            "decision": "reject",
            "thesis": "Insufficient evidence",
            "counter_thesis": "Trend may continue",
            "uncertainties": "Missing market data",
            "evidence": [],
        }

    with SQLiteDatabase(tmp_path / "reject.db") as database:
        result = run_research_cycle(
            client,
            database,
            approved_state(),
            portfolio(),
            RiskLimits(),
            Decimal("100"),
            pm_reviewer=reviewer,
        )
        assert result["decision"] == "rejected"
        assert "Insufficient evidence" in database.decisions.latest()[0].rationale
        assert client.submitted == []


def test_research_pipeline_does_not_submit_when_desk_evidence_is_pending(tmp_path):
    from storage.sqlite import SQLiteDatabase
    from workflows.paper_runtime import run_research_cycle

    client = FakeClient()
    with SQLiteDatabase(tmp_path / "pending.db") as database:
        result = run_research_cycle(
            client, database, approved_state(), portfolio(), RiskLimits(), Decimal("100")
        )
        assert result["decision"] == "pending"
        assert client.submitted == []


def test_paper_runtime_persists_and_reconciles_through_alpaca_adapter(tmp_path):
    from storage.sqlite import SQLiteDatabase
    from workflows.paper_runtime import paper_runtime

    class Client(FakeClient):
        def get_order_by_client_id(self, client_order_id):
            return SimpleNamespace(
                id="broker-1", client_order_id=client_order_id, status="canceled"
            )

    client = Client()
    path = tmp_path / "runtime.db"
    with SQLiteDatabase(path) as database:
        cycle, executor = paper_runtime(client, database)
        result = cycle.run(approved_state(), portfolio(), RiskLimits(), Decimal("100"))
        assert result.submission.broker_order_id == "broker-1"
        request = OrderRequest(
            client_order_id="run-1:AAPL",
            symbol="AAPL",
            quantity=Decimal("10"),
            limit_price=Decimal("100"),
            take_profit_price=Decimal("106"),
            stop_price=Decimal("96"),
        )
        assert executor.reconcile(request).status == "CANCELLED"
    with SQLiteDatabase(path) as database:
        assert database.paper_orders.status("run-1:AAPL") == "CANCELLED"


def test_executor_submits_validated_bracket_to_alpaca():
    client = FakeClient()
    executor = IdempotentPaperExecutor(AlpacaPaperOrders(client))
    order = OrderRequest(
        "run-1:AAPL", "AAPL", Decimal("10"), Decimal("100"), Decimal("110"), Decimal("95")
    )
    decision = RiskDecision(approved=True, quantity=Decimal("10"), reasons=())

    result = executor.submit(order, decision)

    assert result.broker_order_id == "broker-1"
    assert client.submitted[0].client_order_id == order.client_order_id
    assert client.submitted[0].take_profit.limit_price == 110.0
    assert len(client.submitted) == 1
    assert executor.submit(order, decision) == result
    assert len(client.submitted) == 1
