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
