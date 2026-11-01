"""Read Alpaca paper portfolio and persist one snapshot in SQLite."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from brokers.alpaca import AlpacaBroker
from portfolio import persist_portfolio
from storage.sqlite import SQLiteDatabase

_ENV_KEYS = {"ALPACA_API_KEY", "ALPACA_SECRET_KEY", "ALPACA_TRADING_URL"}


def _load_local_env() -> None:
    """Load supported credentials from the project .env without overriding os.environ."""
    candidates = (Path.cwd() / ".env", Path(__file__).resolve().parents[1] / ".env")
    for path in candidates:
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = (part.strip() for part in stripped.split("=", 1))
            if key not in _ENV_KEYS or key in os.environ:
                continue
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            os.environ[key] = value
        return


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("data/trading-agent.db"))
    args = parser.parse_args()

    _load_local_env()
    broker = AlpacaBroker.from_env()
    with SQLiteDatabase(args.database) as database:
        inserted = persist_portfolio(broker, database)
    print(f"Portfolio snapshot: {'inserted' if inserted else 'duplicate'}")


if __name__ == "__main__":
    main()
