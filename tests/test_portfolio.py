from datetime import UTC, datetime
from decimal import Decimal

from brokers.models import Account, Order, Position
from portfolio import collect_portfolio, persist_portfolio
from storage.sqlite import SQLiteDatabase


class FakeBroker:
    def get_account(self):
        return Account(
            "acct", "ACTIVE", "USD", Decimal("1000"), Decimal("1200"), Decimal("1000"), False
        )

    def get_positions(self):
        return (
            Position(
                "AAPL",
                "us_equity",
                "long",
                Decimal("2"),
                Decimal("2"),
                Decimal("100"),
                Decimal("110"),
                Decimal("220"),
                Decimal("20"),
            ),
        )

    def get_orders(self, query=None):
        return (
            Order(
                "order-1",
                "client-1",
                "AAPL",
                "us_equity",
                "buy",
                "market",
                "filled",
                Decimal("2"),
                None,
                Decimal("2"),
                None,
                None,
                Decimal("110"),
                datetime(2026, 11, 1, tzinfo=UTC),
                datetime(2026, 11, 1, tzinfo=UTC),
            ),
        )


def test_portfolio_snapshot_is_canonical_and_deduplicated(tmp_path):
    broker = FakeBroker()
    observed_at = datetime(2026, 11, 1, 12, tzinfo=UTC)

    with SQLiteDatabase(tmp_path / "portfolio.db") as database:
        snapshot = collect_portfolio(broker, observed_at=observed_at)
        assert persist_portfolio(broker, database, observed_at=observed_at) is True
        assert (
            persist_portfolio(broker, database, observed_at=observed_at.replace(minute=13)) is False
        )
        latest = database.broker_snapshots.latest("alpaca")

    assert latest == (observed_at, snapshot.payload())
