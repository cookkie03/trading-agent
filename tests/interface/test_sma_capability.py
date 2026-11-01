from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from data.ingestion import to_stored_price_bar
from data.models import PriceBar
from interface.dashboard import SQLiteDashboardReadModel
from storage.sqlite import SQLiteDatabase


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

    values = SQLiteDashboardReadModel(path).sma("AAPL", window=2)

    assert values == (
        (start + timedelta(days=1), Decimal("11")),
        (start + timedelta(days=2), Decimal("13.5")),
    )


def test_read_model_returns_empty_sma_when_database_is_missing(tmp_path) -> None:
    assert SQLiteDashboardReadModel(tmp_path / "missing.db").sma("AAPL", window=2) == ()


def test_read_model_rejects_non_positive_sma_window(tmp_path) -> None:
    with pytest.raises(ValueError, match="window must be positive"):
        SQLiteDashboardReadModel(tmp_path / "missing.db").sma("AAPL", window=0)
