from decimal import Decimal
from types import SimpleNamespace

from brokers.alpaca_orders import AlpacaPaperOrders, PaperOrderRequest


class FakeClient:
    def __init__(self):
        self.submitted = []
        self.cancelled = []

    def submit_order(self, request):
        self.submitted.append(request)
        return SimpleNamespace(id="broker-1", client_order_id=request.client_order_id)

    def cancel_order_by_id(self, order_id):
        self.cancelled.append(order_id)


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
