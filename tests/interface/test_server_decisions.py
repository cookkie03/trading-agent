import json
from datetime import UTC, datetime
from urllib.request import Request, urlopen

from interface.dashboard import SQLiteDashboardReadModel
from interface.server import DashboardServer
from storage.sqlite import DecisionRecord, SQLiteDatabase


def test_http_dashboard_exposes_persisted_decision_queue(tmp_path):
    database = SQLiteDatabase(tmp_path / "server.db")
    database.decisions.save(
        DecisionRecord(
            client_order_id="run-1:AAPL",
            symbol="AAPL",
            status="risk_approved",
            direction="long",
            conviction="buy",
            rationale="trend confirmed",
            observed_at=datetime(2026, 11, 2, 15, tzinfo=UTC),
            payload="run-1",
        )
    )
    database.close()
    server = DashboardServer(SQLiteDashboardReadModel(tmp_path / "server.db"), port=0)
    server.start()

    try:
        with urlopen(Request(server.url("/api/dashboard"), method="GET")) as response:
            payload = json.load(response)
    finally:
        server.close()

    assert payload["decisions"][0]["symbol"] == "AAPL"
    assert payload["modules"]["decisions"] == "available"
