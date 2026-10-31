"""Sincrona ingestion di market data nel database centrale."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from storage.sqlite import PriceBar as StoredPriceBar
from storage.sqlite import SQLiteDatabase

from .interface import MarketDataProvider
from .models import PriceBar


@dataclass(frozen=True)
class IngestionResult:
    fetched: int
    inserted: int
    duplicates: int


def to_stored_price_bar(bar: PriceBar) -> StoredPriceBar:
    """Map a vendor-neutral bar to the persistence contract once, centrally."""
    return StoredPriceBar(
        symbol=bar.symbol,
        interval=bar.interval,
        timestamp=bar.timestamp,
        open=bar.open,
        high=bar.high,
        low=bar.low,
        close=bar.close,
        volume=bar.volume,
        source=bar.source,
        collected_at=bar.collected_at,
        publication_date=bar.publication_date or bar.collected_at,
        reference_date=bar.reference_date or bar.timestamp,
        raw_payload=bar.raw_payload,
    )


def ingest_ohlcv(
    provider: MarketDataProvider,
    database: SQLiteDatabase,
    *,
    symbol: str,
    start: datetime,
    end: datetime,
    interval: str = "1d",
) -> IngestionResult:
    """Fetch and idempotently persist one symbol's OHLCV history."""
    bars = provider.get_ohlcv_history(symbol, start, end, interval)
    inserted = 0
    with database.transaction():
        for bar in bars:
            if database.market_data.save(to_stored_price_bar(bar)):
                inserted += 1
    return IngestionResult(
        fetched=len(bars),
        inserted=inserted,
        duplicates=len(bars) - inserted,
    )
