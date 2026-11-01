from datetime import UTC, datetime
from decimal import Decimal

from data.ingestion import ingest_ohlcv, to_stored_price_bar
from data.models import PriceBar as ProviderPriceBar
from storage import SQLiteDatabase


class FakeProvider:
    def __init__(self, bars):
        self.bars = bars
        self.calls = []

    def get_ohlcv_history(self, symbol, start, end, interval="1d"):
        self.calls.append((symbol, start, end, interval))
        return self.bars


def provider_bar(timestamp):
    return ProviderPriceBar(
        symbol="AAPL",
        interval="1d",
        timestamp=timestamp,
        open=Decimal("100"),
        high=Decimal("105"),
        low=Decimal("99"),
        close=Decimal("104"),
        volume=Decimal("1234"),
        source="yahoo_finance",
        collected_at=datetime(2026, 10, 31, 20, 0, tzinfo=UTC),
        raw_payload='{"close":"104"}',
    )


def test_to_stored_price_bar_fills_temporal_metadata_from_bar_timestamp():
    timestamp = datetime(2026, 10, 30, tzinfo=UTC)

    stored = to_stored_price_bar(provider_bar(timestamp))

    assert stored.timestamp == timestamp
    assert stored.publication_date == provider_bar(timestamp).collected_at
    assert stored.reference_date == timestamp
    assert stored.source == "yahoo_finance"


def test_ingest_is_idempotent_and_reports_inserted_and_duplicates(tmp_path):
    timestamp = datetime(2026, 10, 30, tzinfo=UTC)
    provider = FakeProvider((provider_bar(timestamp),))
    database = SQLiteDatabase(tmp_path / "trading.sqlite")

    start = datetime(2026, 10, 1, tzinfo=UTC)
    end = datetime(2026, 11, 1, tzinfo=UTC)
    first = ingest_ohlcv(
        provider,
        database,
        symbol="AAPL",
        start=start,
        end=end,
    )
    second = ingest_ohlcv(
        provider,
        database,
        symbol="AAPL",
        start=start,
        end=end,
    )

    assert first.fetched == 1
    assert first.inserted == 1
    assert first.duplicates == 0
    assert second.fetched == 1
    assert second.inserted == 0
    assert second.duplicates == 1
    assert len(database.market_data.list_between("AAPL", "1d", start, end)) == 1
    database.close()
