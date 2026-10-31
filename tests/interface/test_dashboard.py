from datetime import UTC, datetime
from decimal import Decimal
from urllib.request import Request, urlopen

from data.ingestion import to_stored_price_bar
from data.models import PriceBar
from interface.dashboard import (
    ControlSurfaceSnapshot,
    DashboardSnapshot,
    EmptyControlSurfaceReadModel,
    EmptyDashboardReadModel,
    SQLiteDashboardReadModel,
)
from interface.server import DashboardServer
from storage.sqlite import SQLiteDatabase


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


def test_sqlite_read_model_exposes_latest_market_data(tmp_path) -> None:
    timestamp = datetime(2026, 10, 30, tzinfo=UTC)
    bar = PriceBar(
        symbol="AAPL",
        interval="1d",
        timestamp=timestamp,
        open=Decimal("100"),
        high=Decimal("105"),
        low=Decimal("99"),
        close=Decimal("104"),
        volume=Decimal("123"),
        source="openbb:yfinance",
        collected_at=datetime(2026, 10, 31, 16, tzinfo=UTC),
        reference_date=timestamp,
    )
    path = tmp_path / "market.db"
    with SQLiteDatabase(path) as database:
        assert database.market_data.save(to_stored_price_bar(bar)) is True

    snapshot = SQLiteDashboardReadModel(path).snapshot()

    assert snapshot.portfolio.available is False
    assert snapshot.source == "openbb:yfinance"
    assert snapshot.watchlist[0]["symbol"] == "AAPL"
    assert snapshot.watchlist[0]["close"] == "104"
    assert snapshot.modules["market_data"] == "available"


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
