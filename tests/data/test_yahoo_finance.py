from datetime import UTC, datetime
from decimal import Decimal

from trading_agent.data.interface import MarketDataProvider
from trading_agent.data.providers.yahoo_finance import YahooFinanceProvider


class FakeHistory:
    index = [datetime(2024, 1, 2, tzinfo=UTC)]
    columns = ["Open", "High", "Low", "Close", "Volume"]

    def iterrows(self):
        return iter(
            [
                (
                    self.index[0],
                    {
                        "Open": 100.0,
                        "High": 105.0,
                        "Low": 99.0,
                        "Close": 104.0,
                        "Volume": 1234,
                    },
                )
            ]
        )


class FakeTicker:
    def history(self, *, start, end, interval, auto_adjust, actions):
        assert start == datetime(2024, 1, 1, tzinfo=UTC)
        assert end == datetime(2024, 1, 3, tzinfo=UTC)
        assert interval == "1d"
        assert auto_adjust is False
        assert actions is False
        return FakeHistory()


def test_yahoo_finance_history_is_normalized_without_exposing_pandas():
    provider: MarketDataProvider = YahooFinanceProvider(
        ticker_factory=lambda symbol: FakeTicker(),
        clock=lambda: datetime(2024, 1, 3, 12, tzinfo=UTC),
    )

    bars = provider.get_ohlcv_history(
        "AAPL",
        datetime(2024, 1, 1, tzinfo=UTC),
        datetime(2024, 1, 3, tzinfo=UTC),
    )

    assert bars == (
        bars[0].__class__(
            symbol="AAPL",
            interval="1d",
            timestamp=datetime(2024, 1, 2, tzinfo=UTC),
            open=Decimal("100.0"),
            high=Decimal("105.0"),
            low=Decimal("99.0"),
            close=Decimal("104.0"),
            volume=Decimal("1234"),
            source="yahoo_finance",
            collected_at=datetime(2024, 1, 3, 12, tzinfo=UTC),
        ),
    )
