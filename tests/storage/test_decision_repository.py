from datetime import UTC, datetime

from storage.sqlite import DecisionRecord, SQLiteDatabase


def record(order_id="run-1:AAPL", status="risk_approved"):
    return DecisionRecord(
        client_order_id=order_id,
        symbol="AAPL",
        status=status,
        direction="long",
        conviction="buy",
        rationale="trend confirmed",
        observed_at=datetime(2026, 11, 2, 15, tzinfo=UTC),
        payload='{"run_id":"run-1"}',
    )


def test_decision_repository_is_idempotent_and_lists_latest_first(tmp_path):
    database = SQLiteDatabase(tmp_path / "decisions.db")

    assert database.decisions.save(record()) is True
    assert database.decisions.save(record()) is False
    assert database.decisions.latest() == (record(),)


def test_decision_repository_finds_a_decision_by_id_after_reopening(tmp_path):
    path = tmp_path / "decisions.db"
    with SQLiteDatabase(path) as database:
        database.decisions.save(record())
    with SQLiteDatabase(path) as database:
        assert database.decisions.get("run-1:AAPL") == record()
        assert database.decisions.get("missing") is None


def test_decision_repository_keeps_rejected_decision_audit(tmp_path):
    database = SQLiteDatabase(tmp_path / "decisions.db")

    database.decisions.save(record(status="risk_rejected"))

    assert database.decisions.latest()[0].status == "risk_rejected"
