from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from agents.desk_adapters import desk_adapters
from agents.desks import DeskContext
from data.providers.yahoo_fundamentals import FundamentalObservation


def test_fundamental_adapter_preserves_source_evidence_and_oldest_timestamp():
    context = DeskContext(
        symbol="AAPL",
        as_of=datetime(2026, 1, 2).date(),
        current_price=Decimal("1"),
        research=SimpleNamespace(technical_view="neutral", evaluations=()),
        fundamentals=(
            FundamentalObservation(
                "AAPL", "market_cap", Decimal("2"), "source-a", datetime(2026, 1, 1, tzinfo=UTC)
            ),
            FundamentalObservation(
                "AAPL", "revenue", Decimal("3"), "source-b", datetime(2026, 1, 2, tzinfo=UTC)
            ),
        ),
    )
    result = desk_adapters(context)["fundamental"]({"symbol": "AAPL"})
    assert result.role == "fundamental"
    assert result.observed_at == datetime(2026, 1, 1, tzinfo=UTC)
    assert result.content["evidence"] == (
        "source-a | observed 2026-01-01T00:00:00+00:00",
        "source-b | observed 2026-01-02T00:00:00+00:00",
    )


def test_missing_or_naive_source_timestamps_fail_closed():
    context = DeskContext(
        symbol="AAPL",
        as_of=datetime(2026, 1, 2).date(),
        current_price=Decimal("1"),
        research=SimpleNamespace(technical_view="neutral", evaluations=()),
        fundamentals=(
            FundamentalObservation("AAPL", "revenue", Decimal("3"), "source", datetime(2026, 1, 2)),
        ),
    )
    adapters = desk_adapters(context)
    with pytest.raises(ValueError):
        adapters["fundamental"]({"symbol": "AAPL"})
    with pytest.raises(ValueError):
        adapters["market"]({"symbol": "AAPL"})
    with pytest.raises(ValueError, match="symbol"):
        adapters["fundamental"]({"symbol": "MSFT"})
