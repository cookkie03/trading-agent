"""Prova esplicita di compatibilità reale: tre sole richieste di lettura."""

from decimal import Decimal

import pytest

from brokers.alpaca import AlpacaBroker
from brokers.models import OrderQuery


@pytest.mark.integration
def test_existing_paper_account_can_be_read():
    # from_env fallisce con un errore chiaro se il test è richiesto senza credenziali.
    broker = AlpacaBroker.from_env()
    account = broker.get_account()
    positions = broker.get_positions()
    orders = broker.get_orders(OrderQuery(status="all", limit=10))

    assert account.id
    assert account.currency == "USD"
    assert isinstance(account.cash, Decimal)
    assert isinstance(positions, tuple)
    assert len(orders) <= 10
