from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, datetime

from data.models import PriceBar
from storage.sqlite import IndicatorValue, OutboxEvent, SQLiteDatabase

from .indicators import simple_moving_average

SMA_FORMULA_VERSION = "sma-v1"


def sma_parameters(window: int) -> str:
    return json.dumps({"field": "close", "window": window}, sort_keys=True, separators=(",", ":"))


def _watermark(bar: PriceBar) -> str:
    return f"price_bar:{bar.symbol}:{bar.interval}:{bar.timestamp.isoformat()}:{bar.source}"


def _save_sma(
    database: SQLiteDatabase,
    *,
    symbol: str,
    interval: str,
    bars: Sequence[PriceBar],
    window: int,
    calculated_at: datetime,
) -> int:
    parameters = sma_parameters(window)
    averages = simple_moving_average(tuple(bar.close for bar in bars), window=window)
    inserted = 0
    for index, average in enumerate(averages):
        bar = bars[index + window - 1]
        value = IndicatorValue(
            symbol=symbol,
            interval=interval,
            timestamp=bar.timestamp,
            indicator_name="sma",
            parameters=parameters,
            value=average,
            source_watermark=_watermark(bar),
            formula_version=SMA_FORMULA_VERSION,
            status="ready",
            calculated_at=calculated_at.astimezone(UTC),
        )
        if database.indicators.save(value):
            inserted += 1
    return inserted


def materialize_sma_for_event(
    database: SQLiteDatabase,
    event: OutboxEvent,
    *,
    window: int,
    calculated_at: datetime,
) -> int:
    """Materialize SMA values for one committed price-bar event."""
    payload = json.loads(event.payload)
    symbol = str(payload["symbol"])
    interval = str(payload["interval"])
    bars = database.market_data.history(symbol, interval)
    with database.transaction():
        inserted = _save_sma(
            database,
            symbol=symbol,
            interval=interval,
            bars=bars,
            window=window,
            calculated_at=calculated_at,
        )
        database.outbox.mark_processed(event.event_key, calculated_at)
    return inserted


def rebuild_sma(
    database: SQLiteDatabase,
    *,
    symbol: str,
    interval: str = "1d",
    window: int,
    calculated_at: datetime,
) -> int:
    """Rebuild SMA deterministically from all persisted raw bars."""
    bars = database.market_data.history(symbol.upper(), interval)
    with database.transaction():
        return _save_sma(
            database,
            symbol=symbol.upper(),
            interval=interval,
            bars=bars,
            window=window,
            calculated_at=calculated_at,
        )


def process_outbox(
    database: SQLiteDatabase,
    *,
    window: int,
    now: datetime,
    limit: int = 10,
) -> int:
    """Claim and materialize pending price-bar events; safe to repeat."""
    total = 0
    events = database.outbox.claim(limit=limit, now=now)
    for event in events:
        try:
            total += materialize_sma_for_event(database, event, window=window, calculated_at=now)
        except Exception as exc:
            database.outbox.mark_failed(
                event.event_key,
                available_at=now,
                error=f"{type(exc).__name__}: {exc}",
            )
            raise
    return total
