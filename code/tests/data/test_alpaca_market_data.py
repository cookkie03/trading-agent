from datetime import UTC, datetime
from decimal import Decimal

from data.interface import MarketDataProvider
from data.providers.alpaca_market_data import AlpacaMarketDataProvider


class FakeBars:
    data = {
        "AAPL": [
            {
                "timestamp": datetime(2024, 1, 2, tzinfo=UTC),
                "open": 100.0,
                "high": 105.0,
                "low": 99.0,
                "close": 104.0,
                "volume": 1234,
            }
        ]
    }


class FakeClient:
    def __init__(self):
        self.request = None

    def get_stock_bars(self, request):
        self.request = request
        return FakeBars()


def test_alpaca_history_is_normalized_with_explicit_feed():
    client = FakeClient()
    provider: MarketDataProvider = AlpacaMarketDataProvider(
        client=client,
        feed="iex",
        clock=lambda: datetime(2024, 1, 3, 12, tzinfo=UTC),
    )

    bars = provider.get_ohlcv_history(
        "AAPL",
        datetime(2024, 1, 1, tzinfo=UTC),
        datetime(2024, 1, 3, tzinfo=UTC),
    )

    assert len(bars) == 1
    assert bars[0].symbol == "AAPL"
    assert bars[0].timestamp == datetime(2024, 1, 2, tzinfo=UTC)
    assert bars[0].close == Decimal("104.0")
    assert bars[0].volume == Decimal("1234")
    assert bars[0].source == "alpaca:iex"
    assert client.request.symbol_or_symbols == "AAPL"
    assert client.request.feed.value == "iex"
