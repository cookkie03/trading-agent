"""Read Alpaca paper portfolio and persist one snapshot in SQLite."""

from __future__ import annotations

import argparse
from pathlib import Path

from brokers.alpaca import AlpacaBroker
from portfolio import persist_portfolio
from storage.sqlite import SQLiteDatabase


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("data/trading-agent.db"))
    args = parser.parse_args()

    broker = AlpacaBroker.from_env()
    with SQLiteDatabase(args.database) as database:
        inserted = persist_portfolio(broker, database)
    print(f"Portfolio snapshot: {'inserted' if inserted else 'duplicate'}")


if __name__ == "__main__":
    main()
