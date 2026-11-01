"""Materialize persisted indicators from the SQLite outbox."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from analysis.indicator_worker import process_outbox
from storage.sqlite import SQLiteDatabase


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("data/trading-agent.db"))
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    with SQLiteDatabase(args.database) as database:
        inserted = process_outbox(
            database,
            window=args.window,
            limit=args.limit,
            now=datetime.now(UTC),
        )
    print(f"Indicators materialized: {inserted}")


if __name__ == "__main__":
    main()
