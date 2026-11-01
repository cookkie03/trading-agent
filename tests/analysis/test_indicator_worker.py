from datetime import UTC, datetime, timedelta
from decimal import Decimal

from analysis.indicator_worker import process_outbox, rebuild_sma
from data.ingestion import ingest_ohlcv, to_stored_price_bar
from data.models import PriceBar
from storage import SQLiteDatabase


class FakeProvider:
    def __init__(self, bars: tuple[PriceBar, ...]) -> None:
        self.bars = bars

    def get_ohlcv_history(self, symbol, start, end, interval="1d"):
        return self.bars


def test_worker_materializes_sma_and_is_safe_to_repeat(tmp_path) -> None:
    start = datetime(2026, 10, 28, tzinfo=UTC)
    bars = tuple(
        PriceBar(
            symbol="AAPL",
            interval="1d",
            timestamp=start + timedelta(days=index),
            open=Decimal("100"),
            high=Decimal("105"),
            low=Decimal("99"),
            close=close,
            volume=Decimal("100"),
            source="openbb:yfinance",
            collected_at=start + timedelta(days=index, hours=1),
        )
        for index, close in enumerate((Decimal("10"), Decimal("12"), Decimal("15")))
    )
    path = tmp_path / "market.db"
    with SQLiteDatabase(path) as database:
        ingest_ohlcv(
            FakeProvider(bars),
            database,
            symbol="AAPL",
            start=start,
            end=start + timedelta(days=4),
        )
        calculated_at = datetime(2026, 11, 1, 12, tzinfo=UTC)
        assert process_outbox(database, window=2, now=calculated_at) == 2
        assert process_outbox(database, window=2, now=calculated_at) == 0
        values = database.indicators.get_ready(
            "AAPL", "1d", "sma", '{"field":"close","window":2}', "sma-v1"
        )

    assert tuple(value.value for value in values) == (Decimal("11"), Decimal("13.5"))


def test_rebuild_sma_is_deterministic_and_idempotent(tmp_path) -> None:
    start = datetime(2026, 10, 28, tzinfo=UTC)
    bars = tuple(
        PriceBar(
            symbol="AAPL",
            interval="1d",
            timestamp=start + timedelta(days=index),
            open=Decimal("100"),
            high=Decimal("105"),
            low=Decimal("99"),
            close=close,
            volume=Decimal("100"),
            source="openbb:yfinance",
            collected_at=start + timedelta(days=index, hours=1),
        )
        for index, close in enumerate((Decimal("10"), Decimal("12"), Decimal("15")))
    )
    with SQLiteDatabase(tmp_path / "market.db") as database:
        for bar in bars:
            database.market_data.save(to_stored_price_bar(bar))
        now = datetime(2026, 11, 1, 12, tzinfo=UTC)
        assert rebuild_sma(database, symbol="AAPL", window=2, calculated_at=now) == 2
        assert rebuild_sma(database, symbol="AAPL", window=2, calculated_at=now) == 0
