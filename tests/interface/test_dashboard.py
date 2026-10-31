from datetime import UTC, datetime
from urllib.request import Request, urlopen

from trading_agent.interface.dashboard import (
    ControlSurfaceSnapshot,
    DashboardSnapshot,
    EmptyControlSurfaceReadModel,
    EmptyDashboardReadModel,
)
from trading_agent.interface.server import DashboardServer


def test_empty_read_model_explains_unavailable_data() -> None:
    snapshot = EmptyDashboardReadModel().snapshot()

    assert snapshot.source == "not connected"
    assert snapshot.portfolio.available is False
    assert snapshot.portfolio.reason == "Database read model not connected"
    assert snapshot.modules["decisions"] == "unavailable"


def test_empty_control_surface_excludes_mutation_and_secrets() -> None:
    snapshot = EmptyControlSurfaceReadModel().snapshot()

    assert snapshot.source == "not connected"
    assert snapshot.modules == []
    assert "secret" not in str(snapshot.to_dict()).lower()


def test_control_surface_serializes_module_observation() -> None:
    snapshot = ControlSurfaceSnapshot.empty()

    assert snapshot.to_dict()["runtime"]["status"] == "unavailable"
    assert snapshot.to_dict()["config"]["status"] == "unavailable"


def test_snapshot_serializes_stable_read_contract() -> None:
    snapshot = DashboardSnapshot.empty(observed_at=datetime(2026, 10, 31, 12, 0, tzinfo=UTC))

    payload = snapshot.to_dict()

    assert payload["observed_at"] == "2026-10-31T12:00:00+00:00"
    assert payload["portfolio"]["positions"] == []
    assert payload["modules"]["benchmark"] == "post-mvp"


def test_http_server_only_exposes_read_endpoints() -> None:
    server = DashboardServer(
        EmptyDashboardReadModel(),
        control_surface=EmptyControlSurfaceReadModel(),
        port=0,
    )
    server.start()
    try:
        with urlopen(Request(server.url("/api/dashboard"), method="GET")) as response:
            assert response.status == 200
            assert response.headers["content-type"] == "application/json"

        with urlopen(Request(server.url("/api/health"), method="GET")) as response:
            assert response.status == 200

        with urlopen(Request(server.url("/api/control-surface"), method="GET")) as response:
            assert response.status == 200

        try:
            urlopen(Request(server.url("/api/orders"), method="POST"))
        except Exception as error:
            assert getattr(error, "status", None) == 404
        else:
            raise AssertionError("write endpoint unexpectedly exists")
    finally:
        server.close()
