from datetime import UTC, date, datetime
from decimal import Decimal

from data.interface import MarketDataProvider
from data.providers.openbb import OpenBBProvider


class FakeOpenBBResponse:
    def to_df(self):
        return [
            {
                "date": datetime(2024, 1, 2, tzinfo=UTC),
                "open": 100.0,
                "high": 105.0,
                "low": 99.0,
                "close": 104.0,
                "volume": 1234,
            }
        ]


class FakeOpenBBDataFrameResponse:
    def to_df(self):
        return FakeOpenBBDataFrame()


class FakeOpenBBDataFrame:
    def reset_index(self):
        return self

    def to_dict(self, orient):
        assert orient == "records"
        return [
            {
                "Date": datetime(2024, 1, 2, tzinfo=UTC),
                "open": 100.0,
                "high": 105.0,
                "low": 99.0,
                "close": 104.0,
                "volume": 1234,
            }
        ]


class FakeOpenBBEquityPrice:
    def __init__(self, response=None):
        self.response = response or FakeOpenBBResponse()

    def historical(self, *, symbol, start_date, end_date, provider, interval):
        assert symbol == "AAPL"
        assert start_date == "2024-01-01"
        assert end_date == "2024-01-03"
        assert provider == "yfinance"
        assert interval == "1d"
        return self.response


class FakeOpenBBClient:
    equity = type("Equity", (), {"price": FakeOpenBBEquityPrice()})()


class FakeOpenBBDataFrameClient:
    equity = type("Equity", (), {"price": FakeOpenBBEquityPrice(FakeOpenBBDataFrameResponse())})()


def test_openbb_history_is_normalized_without_exposing_openbb_types():
    provider: MarketDataProvider = OpenBBProvider(
        client=FakeOpenBBClient(),
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
    assert bars[0].source == "openbb:yfinance"


def test_openbb_history_normalizes_date_values():
    class DateResponse:
        def to_df(self):
            return [
                {
                    "date": date(2024, 1, 2),
                    "open": 100,
                    "high": 105,
                    "low": 99,
                    "close": 104,
                    "volume": 1234,
                }
            ]

    class DateClient:
        equity = type("Equity", (), {"price": FakeOpenBBEquityPrice(DateResponse())})()

    provider = OpenBBProvider(
        client=DateClient(),
        clock=lambda: datetime(2024, 1, 3, 12, tzinfo=UTC),
    )

    bars = provider.get_ohlcv_history(
        "AAPL",
        datetime(2024, 1, 1, tzinfo=UTC),
        datetime(2024, 1, 3, tzinfo=UTC),
    )

    assert bars[0].timestamp == datetime(2024, 1, 2, tzinfo=UTC)


def test_openbb_history_normalizes_dataframe_date_index():
    provider = OpenBBProvider(
        client=FakeOpenBBDataFrameClient(),
        clock=lambda: datetime(2024, 1, 3, 12, tzinfo=UTC),
    )

    bars = provider.get_ohlcv_history(
        "AAPL",
        datetime(2024, 1, 1, tzinfo=UTC),
        datetime(2024, 1, 3, tzinfo=UTC),
    )

    assert bars[0].timestamp == datetime(2024, 1, 2, tzinfo=UTC)
