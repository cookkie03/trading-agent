"""Populate SQLite with historical OHLCV data from OpenBB."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from data.ingestion import ingest_ohlcv
from data.providers.openbb import OpenBBProvider
from storage.sqlite import SQLiteDatabase


def _datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError("date must include a timezone, for example +00:00")
    return parsed.astimezone(UTC)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("symbol")
    parser.add_argument("--start", required=True, type=_datetime)
    parser.add_argument("--end", required=True, type=_datetime)
    parser.add_argument("--interval", default="1d")
    parser.add_argument("--provider", default="yfinance")
    parser.add_argument("--database", type=Path, default=Path("data/trading-agent.db"))
    args = parser.parse_args()

    provider = OpenBBProvider(provider=args.provider)
    with SQLiteDatabase(args.database) as database:
        result = ingest_ohlcv(
            provider,
            database,
            symbol=args.symbol,
            start=args.start,
            end=args.end,
            interval=args.interval,
        )
    print(
        f"Fetched: {result.fetched}\n"
        f"Inserted: {result.inserted}\n"
        f"Duplicates: {result.duplicates}\n"
        f"Source: openbb:{args.provider}"
    )


if __name__ == "__main__":
    main()
