from datetime import UTC, datetime
from decimal import Decimal

import pytest

from storage import Observation, PriceBar, SQLiteDatabase


@pytest.fixture
def observation() -> Observation:
    return Observation(
        source="vendor-a",
        external_id="ohlcv-AAPL-2026-10-30T20:00:00Z",
        symbol="AAPL",
        metric="close",
        value=Decimal("189.010000000000000001"),
        observed_at=datetime(2026, 10, 30, 20, 0, tzinfo=UTC),
        publication_date=datetime(2026, 10, 30, 20, 1, tzinfo=UTC),
        reference_date=datetime(2026, 10, 30, tzinfo=UTC),
        vendor_record_id="record-7",
        raw_payload='{"close":"189.010000000000000001"}',
    )


def test_observation_round_trip_preserves_decimal_utc_and_provenance(tmp_path, observation):
    database = SQLiteDatabase(tmp_path / "trading.sqlite")
    database.observations.save(observation)

    assert database.observations.get("vendor-a", observation.external_id) == observation
    database.close()

    reopened = SQLiteDatabase(tmp_path / "trading.sqlite")
    assert reopened.observations.get("vendor-a", observation.external_id) == observation
    reopened.close()


def test_duplicate_observation_is_idempotent(observation):
    database = SQLiteDatabase(":memory:")

    assert database.observations.save(observation) is True
    assert database.observations.save(observation) is False
    assert database.observations.count() == 1

    database.close()


def test_transaction_rolls_back_all_observations_on_error():
    database = SQLiteDatabase(":memory:")
    first = Observation.minimal("source", "one", Decimal("1.2"))
    second = Observation.minimal("source", "two", Decimal("2.3"))

    with pytest.raises(RuntimeError):
        with database.transaction():
            database.observations.save(first)
            database.observations.save(second)
            raise RuntimeError("abort")

    assert database.observations.count() == 0
    database.close()


def test_schema_migration_is_versioned():
    database = SQLiteDatabase(":memory:")

    assert database.schema_version == 3
    assert database.migration_names == (
        "001_create_observations",
        "002_create_price_bars",
        "003_create_broker_snapshots",
    )
    database.close()


def test_price_bar_round_trip_and_half_open_interval():
    timestamp = datetime(2026, 10, 30, 20, tzinfo=UTC)
    collected = datetime(2026, 10, 30, 20, 1, tzinfo=UTC)
    bar = PriceBar(
        symbol="AAPL",
        interval="1d",
        timestamp=timestamp,
        open=Decimal("188.10"),
        high=Decimal("190.20"),
        low=Decimal("187.90"),
        close=Decimal("189.010000000000000001"),
        volume=Decimal("1000000"),
        source="yahoo",
        collected_at=collected,
        publication_date=collected,
        reference_date=timestamp,
        raw_payload='{"close":"189.010000000000000001"}',
    )
    database = SQLiteDatabase(":memory:")

    assert database.market_data.save(bar) is True
    assert database.market_data.save(bar) is False
    assert database.market_data.get("AAPL", "1d", timestamp, "yahoo") == bar
    assert database.market_data.list_between("AAPL", "1d", timestamp, collected) == (bar,)
    assert database.market_data.list_between("AAPL", "1d", collected, collected) == ()
    database.close()
