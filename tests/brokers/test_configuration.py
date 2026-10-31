import os

import responses

from trading_agent.brokers.alpaca import AlpacaBroker


@responses.activate
def test_paper_factory_uses_explicit_trading_url():
    responses.get(
        "https://paper-api.alpaca.markets/v2/account",
        json={
            "id": "00000000-0000-4000-8000-000000000001",
            "account_number": "TEST",
            "status": "ACTIVE",
            "currency": "USD",
            "cash": "1000",
            "equity": "1000",
            "buying_power": "1000",
            "trading_blocked": False,
        },
    )

    AlpacaBroker.paper(
        "test-key",
        "test-secret",
        "https://paper-api.alpaca.markets/v2/",
    ).get_account()

    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == "https://paper-api.alpaca.markets/v2/account"


def test_from_env_defaults_to_paper_trading_url(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "test-key")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "test-secret")
    monkeypatch.delenv("ALPACA_TRADING_URL", raising=False)

    broker = AlpacaBroker.from_env()

    assert broker is not None
    assert os.environ["ALPACA_API_KEY"] == "test-key"
