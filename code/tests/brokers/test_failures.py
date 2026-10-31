from datetime import UTC, datetime

import pytest
import responses
from requests.exceptions import Timeout

from brokers.alpaca import AlpacaBroker
from brokers.models import BrokerError, OrderQuery

URL = "https://paper-api.alpaca.markets/v2/positions"


@pytest.mark.parametrize(
    "status,kind",
    [
        (401, "authentication"),
        (403, "authentication"),
        (429, "rate_limit"),
        (503, "unavailable"),
        (422, "invalid_request"),
    ],
)
@responses.activate
def test_http_failures_are_typed_errors_never_empty_positions(status, kind):
    responses.get(URL, status=status, json={"code": 12345, "message": "broker detail"})
    with pytest.raises(BrokerError) as caught:
        AlpacaBroker.paper("test-key", "test-secret").get_positions()
    assert caught.value.kind == kind
    assert caught.value.status_code == status
    assert caught.value.broker_code == "12345"


@responses.activate
def test_network_timeout_is_unavailable_not_an_empty_portfolio():
    responses.get(URL, body=Timeout("connection timed out"))
    with pytest.raises(BrokerError, match="unavailable"):
        AlpacaBroker.paper("test-key", "test-secret").get_positions()


@responses.activate
def test_malformed_payload_is_invalid_response():
    responses.get(URL, json=[{"symbol": "AAPL"}])
    with pytest.raises(BrokerError, match="invalid_response"):
        AlpacaBroker.paper("test-key", "test-secret").get_positions()


@responses.activate
def test_non_finite_amount_is_invalid_response():
    responses.get(
        URL,
        json=[
            {
                "asset_id": "00000000-0000-0000-0000-000000000002",
                "symbol": "AAPL",
                "exchange": "NASDAQ",
                "asset_class": "us_equity",
                "avg_entry_price": "NaN",
                "qty": "1",
                "side": "long",
                "cost_basis": "10",
            }
        ],
    )
    with pytest.raises(BrokerError, match="invalid_response"):
        AlpacaBroker.paper("test-key", "test-secret").get_positions()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"limit": 0},
        {"limit": 501},
        {"limit": True},
        {"status": "filled"},
        {"symbols": ("",)},
        {"after": datetime(2026, 10, 30)},
        {"after": datetime(2026, 10, 31, tzinfo=UTC), "until": datetime(2026, 10, 30, tzinfo=UTC)},
    ],
)
def test_invalid_order_query_is_rejected_before_contacting_broker(kwargs):
    with pytest.raises(ValueError):
        OrderQuery(**kwargs)


def test_missing_paper_credentials_have_clear_error_without_exposing_secrets(monkeypatch):
    monkeypatch.delenv("ALPACA_API_KEY", raising=False)
    monkeypatch.setenv("ALPACA_SECRET_KEY", "sensitive-value")
    with pytest.raises(ValueError) as caught:
        AlpacaBroker.from_env()
    assert "ALPACA_API_KEY" in str(caught.value)
    assert "sensitive-value" not in str(caught.value)


@responses.activate
def test_successful_http_with_invalid_json_is_invalid_response():
    responses.get(URL, body="not valid JSON", status=200, content_type="text/html")
    with pytest.raises(BrokerError) as caught:
        AlpacaBroker.paper("test-key", "test-secret").get_positions()
    assert caught.value.kind == "invalid_response"


def test_paper_factory_bounds_connect_and_read_waits_at_http_boundary(monkeypatch):
    from requests.adapters import HTTPAdapter

    observed_timeouts = []

    def silent_server(self, request, **kwargs):
        observed_timeouts.append(kwargs.get("timeout"))
        raise Timeout("simulated unresponsive server")

    monkeypatch.setattr(HTTPAdapter, "send", silent_server)
    with pytest.raises(BrokerError):
        AlpacaBroker.paper("test-key", "test-secret").get_positions()
    assert observed_timeouts == [(5.0, 30.0)]
