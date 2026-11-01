"""Broker snapshot ingestion into the central SQLite database."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from brokers.interface import Broker
from brokers.models import OrderQuery
from storage.sqlite import SQLiteDatabase


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    return value


@dataclass(frozen=True)
class PortfolioSnapshot:
    account: dict[str, Any]
    positions: tuple[dict[str, Any], ...]
    orders: tuple[dict[str, Any], ...]
    observed_at: datetime

    def payload(self) -> str:
        content = {
            "account": self.account,
            "positions": self.positions,
            "orders": self.orders,
        }
        return json.dumps(_json_value(content), sort_keys=True, separators=(",", ":"))


def collect_portfolio(broker: Broker, *, observed_at: datetime | None = None) -> PortfolioSnapshot:
    account = broker.get_account()
    positions = broker.get_positions()
    orders = broker.get_orders(OrderQuery(status="all", limit=500))
    return PortfolioSnapshot(
        account=_json_value(asdict(account)),
        positions=tuple(_json_value(asdict(position)) for position in positions),
        orders=tuple(_json_value(asdict(order)) for order in orders),
        observed_at=observed_at or datetime.now(UTC),
    )


def persist_portfolio(
    broker: Broker, database: SQLiteDatabase, *, observed_at: datetime | None = None
) -> bool:
    """Collect and persist one broker snapshot; return False for an identical snapshot."""
    snapshot = collect_portfolio(broker, observed_at=observed_at)
    return database.broker_snapshots.save("alpaca", snapshot.observed_at, snapshot.payload())
