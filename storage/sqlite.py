"""SQLite persistence for vendor-neutral observations."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from types import TracebackType
from typing import Self

_SCHEMA_MIGRATIONS: tuple[tuple[str, str], ...] = (
    (
        "001_create_observations",
        """
        CREATE TABLE observations (
            id INTEGER PRIMARY KEY,
            source TEXT NOT NULL,
            external_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            metric TEXT NOT NULL,
            value TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            publication_date TEXT NOT NULL,
            reference_date TEXT NOT NULL,
            vendor_record_id TEXT,
            raw_payload TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE (source, external_id)
        );
        CREATE INDEX observations_symbol_reference
            ON observations (symbol, reference_date);
        """,
    ),
    (
        "002_create_price_bars",
        """
        CREATE TABLE price_bars (
            id INTEGER PRIMARY KEY,
            symbol TEXT NOT NULL,
            interval TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            open TEXT NOT NULL,
            high TEXT NOT NULL,
            low TEXT NOT NULL,
            close TEXT NOT NULL,
            volume TEXT NOT NULL,
            source TEXT NOT NULL,
            collected_at TEXT NOT NULL,
            publication_date TEXT NOT NULL,
            reference_date TEXT NOT NULL,
            raw_payload TEXT NOT NULL,
            UNIQUE (symbol, interval, timestamp, source)
        );
        CREATE INDEX price_bars_lookup
            ON price_bars (symbol, interval, timestamp);
        """,
    ),
)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetimes must include a timezone")
    return value.astimezone(UTC)


def _encode_datetime(value: datetime) -> str:
    return _utc(value).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _decode_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


@dataclass(frozen=True)
class Observation:
    """Osservazione vendor con payload raw e due significati temporali.

    ``observed_at`` indica quando il sistema ha visto il dato; publication e
    reference date descrivono invece il tempo assegnato dal dominio.
    """

    source: str
    external_id: str
    symbol: str
    metric: str
    value: Decimal
    observed_at: datetime
    publication_date: datetime
    reference_date: datetime
    vendor_record_id: str | None = None
    raw_payload: str = "{}"

    def __post_init__(self) -> None:
        for name in ("source", "external_id", "symbol", "metric"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be blank")
        if not isinstance(self.value, Decimal):
            raise TypeError("value must be Decimal")
        for value in (self.observed_at, self.publication_date, self.reference_date):
            _utc(value)

    @classmethod
    def minimal(cls, source: str, external_id: str, value: Decimal) -> Self:
        timestamp = datetime.now(UTC)
        return cls(
            source=source,
            external_id=external_id,
            symbol="UNKNOWN",
            metric="value",
            value=value,
            observed_at=timestamp,
            publication_date=timestamp,
            reference_date=timestamp,
        )


@dataclass(frozen=True)
class PriceBar:
    """Barra OHLCV normalizzata e indipendente dal provider."""

    symbol: str
    interval: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    source: str
    collected_at: datetime
    publication_date: datetime
    reference_date: datetime
    raw_payload: str = "{}"

    def __post_init__(self) -> None:
        for name in ("symbol", "interval", "source"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be blank")
        for value in (
            self.open,
            self.high,
            self.low,
            self.close,
            self.volume,
        ):
            if not isinstance(value, Decimal):
                raise TypeError("OHLCV values must be Decimal")
        for timestamp in (
            self.timestamp,
            self.collected_at,
            self.publication_date,
            self.reference_date,
        ):
            _utc(timestamp)
        if self.high < self.low:
            raise ValueError("high must be greater than or equal to low")


class ObservationRepository:
    """Persistenza idempotente delle osservazioni vendor."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def save(self, observation: Observation) -> bool:
        owns_transaction = not self._connection.in_transaction
        if owns_transaction:
            self._connection.execute("BEGIN")
        try:
            cursor = self._connection.execute(
                """
                INSERT OR IGNORE INTO observations (
                    source, external_id, symbol, metric, value, observed_at,
                    publication_date, reference_date, vendor_record_id,
                    raw_payload, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    observation.source,
                    observation.external_id,
                    observation.symbol,
                    observation.metric,
                    str(observation.value),
                    _encode_datetime(observation.observed_at),
                    _encode_datetime(observation.publication_date),
                    _encode_datetime(observation.reference_date),
                    observation.vendor_record_id,
                    observation.raw_payload,
                    _encode_datetime(datetime.now(UTC)),
                ),
            )
            if owns_transaction:
                self._connection.commit()
            return cursor.rowcount == 1
        except Exception:
            if owns_transaction:
                self._connection.rollback()
            raise

    def get(self, source: str, external_id: str) -> Observation | None:
        row = self._connection.execute(
            "SELECT * FROM observations WHERE source = ? AND external_id = ?",
            (source, external_id),
        ).fetchone()
        if row is None:
            return None
        return Observation(
            source=row["source"],
            external_id=row["external_id"],
            symbol=row["symbol"],
            metric=row["metric"],
            value=Decimal(row["value"]),
            observed_at=_decode_datetime(row["observed_at"]),
            publication_date=_decode_datetime(row["publication_date"]),
            reference_date=_decode_datetime(row["reference_date"]),
            vendor_record_id=row["vendor_record_id"],
            raw_payload=row["raw_payload"],
        )

    def count(self) -> int:
        return int(self._connection.execute("SELECT count(*) FROM observations").fetchone()[0])


class MarketDataRepository:
    """Persistenza idempotente delle barre con chiave di provenienza."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def save(self, bar: PriceBar) -> bool:
        cursor = self._connection.execute(
            """
            INSERT OR IGNORE INTO price_bars (
                symbol, interval, timestamp, open, high, low, close, volume,
                source, collected_at, publication_date, reference_date, raw_payload
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                bar.symbol,
                bar.interval,
                _encode_datetime(bar.timestamp),
                str(bar.open),
                str(bar.high),
                str(bar.low),
                str(bar.close),
                str(bar.volume),
                bar.source,
                _encode_datetime(bar.collected_at),
                _encode_datetime(bar.publication_date),
                _encode_datetime(bar.reference_date),
                bar.raw_payload,
            ),
        )
        if not self._connection.in_transaction:
            self._connection.commit()
        return cursor.rowcount == 1

    def get(self, symbol: str, interval: str, timestamp: datetime, source: str) -> PriceBar | None:
        row = self._connection.execute(
            """
            SELECT * FROM price_bars
            WHERE symbol = ? AND interval = ? AND timestamp = ? AND source = ?
            """,
            (symbol, interval, _encode_datetime(timestamp), source),
        ).fetchone()
        return self._from_row(row) if row is not None else None

    def latest(self, symbol: str, interval: str = "1d") -> PriceBar | None:
        row = self._connection.execute(
            """
            SELECT * FROM price_bars
            WHERE symbol = ? AND interval = ?
            ORDER BY timestamp DESC LIMIT 1
            """,
            (symbol, interval),
        ).fetchone()
        return self._from_row(row) if row is not None else None

    def symbols(self) -> tuple[str, ...]:
        rows = self._connection.execute(
            "SELECT DISTINCT symbol FROM price_bars ORDER BY symbol"
        ).fetchall()
        return tuple(row[0] for row in rows)

    def list_between(
        self, symbol: str, interval: str, start: datetime, end: datetime
    ) -> tuple[PriceBar, ...]:
        rows = self._connection.execute(
            """
            SELECT * FROM price_bars
            WHERE symbol = ? AND interval = ? AND timestamp >= ? AND timestamp < ?
            ORDER BY timestamp
            """,
            (symbol, interval, _encode_datetime(start), _encode_datetime(end)),
        ).fetchall()
        return tuple(self._from_row(row) for row in rows)

    @staticmethod
    def _from_row(row: sqlite3.Row) -> PriceBar:
        return PriceBar(
            symbol=row["symbol"],
            interval=row["interval"],
            timestamp=_decode_datetime(row["timestamp"]),
            open=Decimal(row["open"]),
            high=Decimal(row["high"]),
            low=Decimal(row["low"]),
            close=Decimal(row["close"]),
            volume=Decimal(row["volume"]),
            source=row["source"],
            collected_at=_decode_datetime(row["collected_at"]),
            publication_date=_decode_datetime(row["publication_date"]),
            reference_date=_decode_datetime(row["reference_date"]),
            raw_payload=row["raw_payload"],
        )


class SQLiteDatabase:
    """Gateway SQLite: i chiamanti usano repository, non SQL diretto.

    Le migrazioni sono applicate all'apertura e la transazione resta il punto
    esplicito per raggruppare scritture atomiche.
    """

    def __init__(self, path: str | Path) -> None:
        self._connection = sqlite3.connect(str(path), isolation_level=None)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._migrate()
        self.observations = ObservationRepository(self._connection)
        self.market_data = MarketDataRepository(self._connection)

    @property
    def schema_version(self) -> int:
        return int(self._connection.execute("PRAGMA user_version").fetchone()[0])

    @property
    def migration_names(self) -> tuple[str, ...]:
        return tuple(name for name, _ in _SCHEMA_MIGRATIONS[: self.schema_version])

    @contextmanager
    def transaction(self) -> Iterator[Self]:
        if self._connection.in_transaction:
            raise RuntimeError("nested transactions are not supported")
        self._connection.execute("BEGIN")
        try:
            yield self
        except Exception:
            self._connection.rollback()
            raise
        else:
            self._connection.commit()

    def _migrate(self) -> None:
        current = self.schema_version
        if current > len(_SCHEMA_MIGRATIONS):
            raise RuntimeError("database schema is newer than this application")
        for version, (_, sql) in enumerate(_SCHEMA_MIGRATIONS[current:], current + 1):
            self._connection.execute("BEGIN")
            try:
                self._connection.executescript(sql)
                self._connection.execute(f"PRAGMA user_version = {version}")
                self._connection.commit()
            except Exception:
                self._connection.rollback()
                raise

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
