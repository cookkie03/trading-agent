from datetime import UTC, datetime
from decimal import Decimal

from data.interface import MarketDataProvider
from data.models import FundamentalMetrics, MacroObservation
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


class FakeOpenBBEquityPrice:
    def historical(self, *, symbol, start_date, end_date, provider, interval):
        assert symbol == "AAPL"
        assert start_date == "2024-01-01"
        assert end_date == "2024-01-03"
        assert provider == "yfinance"
        assert interval == "1d"
        return FakeOpenBBResponse()


class FakeOpenBBClient:
    equity = type("Equity", (), {"price": FakeOpenBBEquityPrice()})()


def test_openbb_fundamentals_are_normalized_without_exposing_openbb_types():
    class FakeFundamentalResponse:
        def to_df(self):
            return [{"symbol": "AAPL", "currency": "USD", "pe_ratio": 39.5, "beta": None}]

    class FakeFundamental:
        def metrics(self, *, symbol, provider):
            assert symbol == "AAPL"
            assert provider == "yfinance"
            return FakeFundamentalResponse()

    class FakeOpenBBClientWithFundamentals(FakeOpenBBClient):
        equity = type(
            "Equity",
            (),
            {"fundamental": FakeFundamental()},
        )()

    provider = OpenBBProvider(
        client=FakeOpenBBClientWithFundamentals(),
        clock=lambda: datetime(2024, 1, 3, 12, tzinfo=UTC),
    )

    metrics = provider.get_fundamental_metrics(" aapl ")

    assert isinstance(metrics, FundamentalMetrics)
    assert metrics.symbol == "AAPL"
    assert metrics.values == {"pe_ratio": Decimal("39.5"), "beta": None}
    assert metrics.source == "openbb:yfinance"


def test_openbb_macro_series_is_normalized_without_exposing_openbb_types():
    class FakeMacroResponse:
        def to_df(self):
            return [
                {"date": datetime(2024, 1, 1, tzinfo=UTC), "GDP": 27000.1},
                {"date": datetime(2024, 4, 1, tzinfo=UTC), "GDP": 27200.2},
            ]

    class FakeEconomy:
        def fred_series(self, *, symbol, provider):
            assert symbol == "GDP"
            assert provider == "fred"
            return FakeMacroResponse()

    class FakeOpenBBClientWithMacro:
        economy = FakeEconomy()

    provider = OpenBBProvider(
        client=FakeOpenBBClientWithMacro(),
        provider="fred",
        clock=lambda: datetime(2024, 7, 1, 12, tzinfo=UTC),
    )

    series = provider.get_macro_series(" gdp ")

    assert isinstance(series, MacroObservation)
    assert series.series == "GDP"
    assert series.observations == (
        (datetime(2024, 1, 1, tzinfo=UTC), Decimal("27000.1")),
        (datetime(2024, 4, 1, tzinfo=UTC), Decimal("27200.2")),
    )
    assert series.source == "openbb:fred"


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
