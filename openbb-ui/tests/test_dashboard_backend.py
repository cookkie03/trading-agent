import json
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from openbb_ui.backend.models import DashboardReadModel, EmptyDashboardReadModel, SqliteDashboardReadModel
from openbb_ui.backend.server import DashboardServer
from storage.sqlite import SqliteObservationStorage


def test_empty_dashboard_read_model_contract() -> None:
    model = EmptyDashboardReadModel()
    snapshot = model.snapshot()
    assert snapshot.source == "not connected"
    assert snapshot.freshness == "not available"
    assert snapshot.portfolio.available is False
    assert snapshot.portfolio.reason == "Database read model not connected"
    assert snapshot.watchlist == []
    assert snapshot.modules["openbb_api"] == "unreachable"
    assert snapshot.modules["benchmark"] == "post-mvp"


def test_sqlite_read_model_with_real_observations() -> None:
    with TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "market.db"
        storage = SqliteObservationStorage(db_path)
        storage.initialize_schema()
        storage.record_observation(
            source="alpaca",
            external_id="obs-1",
            symbol="AAPL",
            metric="close",
            value="150.25",
            observed_at="2026-10-31T12:00:00+00:00",
            publication_date="2026-10-31",
            reference_date="2026-10-31",
            vendor_record_id="rec-1",
            raw_payload="{}",
        )

        model = SqliteDashboardReadModel(db_path=db_path)
        snapshot = model.snapshot()

        assert snapshot.source == f"sqlite:{db_path}"
        assert snapshot.freshness != "not available"
        assert len(snapshot.observations) == 1
        assert snapshot.observations[0]["symbol"] == "AAPL"
        assert snapshot.observations[0]["value"] == "150.25"
        assert snapshot.portfolio.available is False
        assert "no brokerage/portfolio sync configured" in snapshot.portfolio.reason.lower()


def test_server_http_seams_read_only_and_no_secrets() -> None:
    static_dir = Path("/tmp/empty_static")
    static_dir.mkdir(parents=True, exist_ok=True)
    (static_dir / "index.html").write_text("<!doctype html><html><body>UI</body></html>")

    model = EmptyDashboardReadModel()
    server = DashboardServer(read_model=model, host="[IP_REDACTED]", port=0, static_dir=static_dir)
    server.start()
    try:
        url_dashboard = server.url("/api/dashboard")
        with urlopen(Request(url_dashboard, method="GET")) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode())
            assert data["portfolio"]["available"] is False
            assert "secret" not in json.dumps(data).lower()
            assert "token" not in json.dumps(data).lower()

        with urlopen(Request(server.url("/api/health"), method="GET")) as resp:
            assert resp.status == 200
            health = json.loads(resp.read().decode())
            assert health["status"] == "ok"
            assert health["read_only"] is True

        # Mutating requests must return 404/405 (never execute mutation)
        req = Request(server.url("/api/orders"), method="POST", data=b"{}")
        try:
            urlopen(req)
            assert False, "Mutation request should fail"
        except HTTPError as e:
            assert e.code in (404, 405)

        with urlopen(Request(server.url("/"), method="GET")) as resp:
            assert resp.status == 200
            html = resp.read().decode()
            assert "UI" in html
    finally:
        server.stop()
