from datetime import UTC, datetime
from decimal import Decimal

from data.ingestion import ingest_ohlcv, to_stored_price_bar
from data.models import PriceBar
from storage.sqlite import SQLiteDatabase


class FakeProvider:
    def __init__(self, bars: tuple[PriceBar, ...]) -> None:
        self.bars = bars

    def get_ohlcv_history(self, symbol, start, end, interval="1d"):
        return self.bars


def make_bar(*, source="openbb:yfinance") -> PriceBar:
    collected = datetime(2026, 10, 31, 16, tzinfo=UTC)
    timestamp = datetime(2026, 10, 30, tzinfo=UTC)
    return PriceBar(
        symbol="AAPL",
        interval="1d",
        timestamp=timestamp,
        open=Decimal("100.00"),
        high=Decimal("105.00"),
        low=Decimal("99.00"),
        close=Decimal("104.00"),
        volume=Decimal("123"),
        source=source,
        collected_at=collected,
        raw_payload='{"close": 104}',
    )


def test_bridge_defaults_dates_without_losing_provenance() -> None:
    stored = to_stored_price_bar(make_bar())

    assert stored.reference_date == stored.timestamp
    assert stored.publication_date == stored.collected_at
    assert stored.source == "openbb:yfinance"
    assert stored.raw_payload == '{"close": 104}'


def test_ingestion_is_idempotent_and_persists_price_bar(tmp_path) -> None:
    bar = make_bar()
    provider = FakeProvider((bar,))
    start = datetime(2026, 10, 1, tzinfo=UTC)
    end = datetime(2026, 11, 1, tzinfo=UTC)

    with SQLiteDatabase(tmp_path / "market.db") as database:
        first = ingest_ohlcv(provider, database, symbol="AAPL", start=start, end=end)
        second = ingest_ohlcv(provider, database, symbol="AAPL", start=start, end=end)

        assert first == second.__class__(fetched=1, inserted=1, duplicates=0)
        assert second.fetched == 1
        assert second.inserted == 0
        assert second.duplicates == 1
        assert len(database.market_data.list_between("AAPL", "1d", start, end)) == 1
