from datetime import UTC, datetime

from interface.dashboard import (
    DashboardSnapshot,
    DecisionReadModel,
    PortfolioReadModel,
    SQLiteDashboardReadModel,
)
from storage.sqlite import DecisionRecord, SQLiteDatabase


def test_dashboard_snapshot_exposes_explicit_decision_state():
    snapshot = DashboardSnapshot(
        observed_at=datetime(2026, 11, 2, 15, tzinfo=UTC),
        source="sqlite",
        freshness="fresh",
        portfolio=PortfolioReadModel(available=False, reason="not synced"),
        decisions=(
            DecisionReadModel(
                symbol="AAPL",
                status="risk_approved",
                direction="long",
                conviction="buy",
                observed_at="2026-11-02T15:00:00+00:00",
                rationale="trend confirmed",
            ),
        ),
    )

    payload = snapshot.to_dict()

    assert payload["decisions"][0]["status"] == "risk_approved"
    assert payload["decisions"][0]["direction"] == "long"


def test_empty_snapshot_does_not_fabricate_decisions():
    assert DashboardSnapshot.empty().decisions == ()


def test_sqlite_dashboard_reads_persisted_decisions(tmp_path):
    database = SQLiteDatabase(tmp_path / "dashboard.db")
    database.decisions.save(
        DecisionRecord(
            client_order_id="run-1:AAPL",
            symbol="AAPL",
            status="risk_approved",
            direction="long",
            conviction="buy",
            rationale="trend confirmed",
            observed_at=datetime(2026, 11, 2, 15, tzinfo=UTC),
            payload='{"run_id":"run-1"}',
        )
    )
    database.close()

    snapshot = SQLiteDashboardReadModel(tmp_path / "dashboard.db").snapshot()

    assert snapshot.decisions[0].symbol == "AAPL"
    assert snapshot.modules["decisions"] == "available"
