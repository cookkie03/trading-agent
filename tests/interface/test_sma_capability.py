from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from analysis.indicator_worker import process_outbox
from data.ingestion import to_stored_price_bar
from data.models import PriceBar
from interface.dashboard import SQLiteDashboardReadModel
from storage.sqlite import OutboxEvent, SQLiteDatabase


def test_read_model_calculates_sma_from_persisted_bars(tmp_path) -> None:
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
        for bar in bars:
            assert database.market_data.save(to_stored_price_bar(bar)) is True
        database.outbox.enqueue(
            OutboxEvent(
                event_key="price_bar:AAPL:1d:2026-10-30T00:00:00Z:openbb:yfinance",
                event_type="price_bar.committed",
                payload='{"interval":"1d","symbol":"AAPL"}',
                created_at=start + timedelta(days=2),
            )
        )
        assert (
            process_outbox(
                database,
                window=2,
                now=datetime(2026, 11, 1, 12, tzinfo=UTC),
            )
            == 2
        )

    values = SQLiteDashboardReadModel(path).sma("AAPL", window=2)

    assert values == (
        (start + timedelta(days=1), Decimal("11")),
        (start + timedelta(days=2), Decimal("13.5")),
    )


def test_read_model_does_not_calculate_sma_from_raw_data_without_worker(tmp_path) -> None:
    start = datetime(2026, 10, 28, tzinfo=UTC)
    path = tmp_path / "market.db"
    with SQLiteDatabase(path) as database:
        database.market_data.save(
            to_stored_price_bar(
                PriceBar(
                    symbol="AAPL",
                    interval="1d",
                    timestamp=start,
                    open=Decimal("100"),
                    high=Decimal("105"),
                    low=Decimal("99"),
                    close=Decimal("10"),
                    volume=Decimal("100"),
                    source="openbb:yfinance",
                    collected_at=start,
                )
            )
        )

    assert SQLiteDashboardReadModel(path).sma("AAPL", window=1) == ()


def test_read_model_returns_empty_sma_when_database_is_missing(tmp_path) -> None:
    assert SQLiteDashboardReadModel(tmp_path / "missing.db").sma("AAPL", window=2) == ()


def test_read_model_rejects_non_positive_sma_window(tmp_path) -> None:
    with pytest.raises(ValueError, match="window must be positive"):
        SQLiteDashboardReadModel(tmp_path / "missing.db").sma("AAPL", window=0)
