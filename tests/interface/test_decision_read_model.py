from datetime import UTC, datetime

from interface.dashboard import DashboardSnapshot, DecisionReadModel, PortfolioReadModel


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
