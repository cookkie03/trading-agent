"""Test del contratto pubblico, attraverso il vero SDK e HTTP simulato."""

from decimal import Decimal

import responses

from trading_agent.brokers.alpaca import AlpacaBroker

PAPER_URL = "https://paper-api.alpaca.markets"


@responses.activate
def test_account_preserves_money_and_distinguishes_cash_from_buying_power():
    responses.get(
        f"{PAPER_URL}/v2/account",
        json={
            "id": "00000000-0000-0000-0000-000000000001",
            "account_number": "TEST",
            "status": "ACTIVE",
            "currency": "USD",
            "cash": "1234.567890123456789",
            "equity": "2234.56",
            "buying_power": "8000.00",
            "regt_buying_power": "4000",
            "daytrading_buying_power": "8000",
            "non_marginable_buying_power": "1234",
            "accrued_fees": "0",
            "pending_transfer_out": "0",
            "portfolio_value": "2234.56",
            "pattern_day_trader": False,
            "trading_blocked": False,
            "transfers_blocked": False,
            "account_blocked": False,
            "created_at": "2026-10-01T12:00:00Z",
            "trade_suspended_by_user": False,
            "multiplier": "2",
            "shorting_enabled": True,
            "long_market_value": "1000",
            "short_market_value": "0",
            "initial_margin": "0",
            "maintenance_margin": "0",
            "last_equity": "2234",
            "last_maintenance_margin": "0",
            "sma": "0",
            "daytrade_count": 0,
        },
    )
    broker = AlpacaBroker.paper("test-key", "test-secret")

    account = broker.get_account()

    assert account.id == "00000000-0000-0000-0000-000000000001"
    assert account.cash == Decimal("1234.567890123456789")
    assert account.buying_power == Decimal("8000.00")
    assert account.equity == Decimal("2234.56")
    assert account.currency == "USD"
    assert account.status == "ACTIVE"
    assert account.trading_blocked is False
    assert all(call.request.method == "GET" for call in responses.calls)


@responses.activate
def test_positions_preserve_short_quantity_and_absent_market_prices():
    responses.get(
        f"{PAPER_URL}/v2/positions",
        json=[
            {
                "asset_id": "00000000-0000-0000-0000-000000000002",
                "symbol": "AAPL",
                "exchange": "NASDAQ",
                "asset_class": "us_equity",
                "avg_entry_price": "210.125",
                "qty": "-2.5",
                "qty_available": "-1.5",
                "side": "short",
                "cost_basis": "-525.3125",
                "market_value": None,
                "current_price": None,
                "unrealized_pl": None,
            }
        ],
    )

    positions = AlpacaBroker.paper("test-key", "test-secret").get_positions()

    assert len(positions) == 1
    assert positions[0].symbol == "AAPL"
    assert positions[0].quantity == Decimal("-2.5")
    assert positions[0].quantity_available == Decimal("-1.5")
    assert positions[0].average_entry_price == Decimal("210.125")
    assert positions[0].side == "short"
    assert positions[0].asset_class == "us_equity"
    assert positions[0].current_price is None
    assert positions[0].market_value is None
    assert positions[0].unrealized_profit_loss is None


@responses.activate
def test_account_without_positions_returns_empty_tuple():
    responses.get(f"{PAPER_URL}/v2/positions", json=[])
    assert AlpacaBroker.paper("test-key", "test-secret").get_positions() == ()


def order_payload(**changes):
    payload = {
        "id": "00000000-0000-0000-0000-000000000010",
        "client_order_id": "research-10",
        "symbol": "AAPL",
        "asset_class": "us_equity",
        "created_at": "2026-10-30T14:00:00Z",
        "updated_at": "2026-10-30T14:01:00Z",
        "submitted_at": "2026-10-30T14:00:00Z",
        "filled_at": None,
        "order_class": "bracket",
        "type": "limit",
        "side": "buy",
        "time_in_force": "day",
        "status": "partially_filled",
        "extended_hours": False,
        "qty": "10",
        "notional": None,
        "filled_qty": "3",
        "limit_price": "201.10",
        "stop_price": None,
        "filled_avg_price": "201.05",
        "legs": None,
    }
    return payload | changes


@responses.activate
def test_orders_preserve_partial_fills_and_nested_protection_orders():
    from datetime import UTC, datetime

    from trading_agent.brokers.models import OrderQuery

    stop = order_payload(
        id="00000000-0000-0000-0000-000000000011",
        client_order_id="stop-11",
        order_class="simple",
        type="stop",
        side="sell",
        status="held",
        filled_qty="0",
        stop_price="195.00",
        limit_price=None,
        filled_avg_price=None,
    )
    responses.get(f"{PAPER_URL}/v2/orders", json=[order_payload(legs=[stop])])

    orders = AlpacaBroker.paper("test-key", "test-secret").get_orders(
        OrderQuery(
            status="all", symbols=("AAPL",), limit=20, after=datetime(2026, 10, 1, tzinfo=UTC)
        )
    )

    assert orders[0].quantity == Decimal("10")
    assert orders[0].filled_quantity == Decimal("3")
    assert orders[0].average_fill_price == Decimal("201.05")
    assert orders[0].status == "partially_filled"
    assert orders[0].submitted_at == datetime(2026, 10, 30, 14, tzinfo=UTC)
    assert orders[0].legs[0].status == "held"
    assert orders[0].legs[0].stop_price == Decimal("195")
    assert orders[0].legs[0].limit_price is None
    from urllib.parse import parse_qs, urlparse

    params = parse_qs(urlparse(responses.calls[0].request.url).query)
    assert params["status"] == ["all"]
    assert params["limit"] == ["20"]
    assert params["symbols"] == ["AAPL"]
    assert params["nested"] == ["True"]
    assert params["direction"] == ["desc"]
    assert "2026-10-01" in params["after"][0]


@responses.activate
def test_no_orders_returns_empty_tuple_and_uses_explicit_bounded_query():
    responses.get(f"{PAPER_URL}/v2/orders", json=[])
    assert AlpacaBroker.paper("test-key", "test-secret").get_orders() == ()
    assert "status=open" in responses.calls[0].request.url
    assert "limit=100" in responses.calls[0].request.url
