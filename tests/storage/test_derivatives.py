from datetime import UTC, datetime
from decimal import Decimal

from storage import IndicatorValue, OutboxEvent, SQLiteDatabase


def test_indicator_value_is_idempotent_and_preserves_provenance() -> None:
    database = SQLiteDatabase(":memory:")
    value = IndicatorValue(
        symbol="AAPL",
        interval="1d",
        timestamp=datetime(2026, 10, 30, tzinfo=UTC),
        indicator_name="sma",
        parameters='{"window":20,"field":"close"}',
        value=Decimal("231.42"),
        source_watermark="price_bar:AAPL:1d:2026-10-30T00:00:00Z:openbb:yfinance",
        formula_version="sma-v1",
        status="ready",
        calculated_at=datetime(2026, 11, 1, 12, tzinfo=UTC),
    )

    assert database.indicators.save(value) is True
    assert database.indicators.save(value) is False
    assert database.indicators.get_ready("AAPL", "1d", "sma", value.parameters, "sma-v1") == (
        value,
    )


def test_outbox_event_is_idempotent_and_claimable() -> None:
    database = SQLiteDatabase(":memory:")
    event = OutboxEvent(
        event_key="price_bar:AAPL:1d:2026-10-30T00:00:00Z:openbb:yfinance",
        event_type="price_bar.committed",
        payload='{"symbol":"AAPL"}',
        created_at=datetime(2026, 11, 1, 12, tzinfo=UTC),
    )

    assert database.outbox.enqueue(event) is True
    assert database.outbox.enqueue(event) is False
    claimed = database.outbox.claim(limit=1, now=datetime(2026, 11, 1, 12, 1, tzinfo=UTC))
    assert len(claimed) == 1
    assert claimed[0].event_key == event.event_key
    assert claimed[0].attempts == 1
    assert claimed[0].claimed_at == datetime(2026, 11, 1, 12, 1, tzinfo=UTC)
    database.outbox.mark_processed(event.event_key, datetime(2026, 11, 1, 12, 2, tzinfo=UTC))
    assert database.outbox.claim(limit=1, now=datetime(2026, 11, 1, 12, 3, tzinfo=UTC)) == ()
