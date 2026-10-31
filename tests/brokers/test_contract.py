from decimal import Decimal

import pytest
import responses

from brokers.alpaca import AlpacaBroker
from brokers.interface import Broker
from brokers.models import Account
from tests.fakes.broker import EmptyBroker


@pytest.mark.parametrize("implementation", ["fake", "alpaca"])
@responses.activate
def test_empty_account_is_readable_through_same_broker_contract(implementation):
    account = Account(
        id="00000000-0000-0000-0000-000000000001",
        status="ACTIVE",
        currency="USD",
        cash=Decimal("1000.01"),
        equity=Decimal("1000.01"),
        buying_power=Decimal("2000.02"),
        trading_blocked=False,
    )
    broker: Broker
    if implementation == "fake":
        broker = EmptyBroker(account)
    else:
        url = "https://paper-api.alpaca.markets/v2"
        responses.get(
            f"{url}/account",
            json={
                "id": account.id,
                "account_number": "TEST",
                "status": "ACTIVE",
                "currency": "USD",
                "cash": "1000.01",
                "equity": "1000.01",
                "buying_power": "2000.02",
                "trading_blocked": False,
            },
        )
        responses.get(f"{url}/positions", json=[])
        responses.get(f"{url}/orders", json=[])
        broker = AlpacaBroker.paper("test-key", "test-secret")
    assert broker.get_account() == account
    assert broker.get_positions() == ()
    assert broker.get_orders() == ()
