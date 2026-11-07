from datetime import UTC, datetime, timedelta

import pytest

from agents.graph import Analysis, build_agent_graph
from agents.risk_adapter import proposal_complete, risk_gate


def run_graph(proposal, portfolio):
    now = datetime(2026, 11, 5, tzinfo=UTC)
    roles = ("market", "sentiment", "technical", "fundamental", "risk")
    graph = build_agent_graph(
        analysts={
            role: lambda context, role=role: Analysis(role, now, {"summary": "ok"})
            for role in roles
        },
        portfolio_manager=lambda context: proposal,
        risk_gate=risk_gate,
        proposal_complete=proposal_complete,
        max_age=timedelta(hours=1),
    )
    return graph.invoke({"context": {"symbol": "AAPL", "portfolio": portfolio}, "now": now})


def test_graph_applies_real_risk_veto():
    proposal = {
        "decision": "approve",
        "symbol": "AAPL",
        "direction": "long",
        "quantity": "100",
        "entry_price": "100",
        "stop_price": "95",
    }
    portfolio = {"equity": "10000", "cash": "10000", "open_risk": "0", "symbol_exposure": "0"}
    assert run_graph(proposal, portfolio)["decision"] == "rejected"


def test_incomplete_proposal_stays_pending():
    result = run_graph({"decision": "approve", "symbol": "AAPL"}, {})
    assert result["decision"] == "pending"


def test_valid_trade_is_approved():
    proposal = {
        "decision": "approve",
        "symbol": "AAPL",
        "direction": "long",
        "quantity": "5",
        "entry_price": "100",
        "stop_price": "95",
    }
    portfolio = {"equity": "10000", "cash": "10000", "open_risk": "0", "symbol_exposure": "0"}
    assert run_graph(proposal, portfolio)["decision"] == "approved"


@pytest.mark.parametrize("value", [None, True, "NaN", "Infinity", "invalid", -1, {}, []])
def test_invalid_portfolio_values_fail_closed(value):
    proposal = {
        "symbol": "AAPL",
        "direction": "long",
        "quantity": "5",
        "entry_price": "100",
        "stop_price": "95",
    }
    portfolio = {"equity": value, "cash": "10000", "open_risk": "0", "symbol_exposure": "0"}
    assert risk_gate({"proposal": proposal, "symbol": "AAPL", "portfolio": portfolio}) is False


@pytest.mark.parametrize("value", [None, True, "NaN", "Infinity", "invalid", -1, {}, []])
def test_invalid_proposal_values_fail_closed(value):
    proposal = {
        "symbol": "AAPL",
        "direction": "long",
        "quantity": value,
        "entry_price": "100",
        "stop_price": "95",
    }
    assert proposal_complete(proposal) is False
    assert risk_gate({"proposal": proposal, "symbol": "AAPL", "portfolio": {}}) is False


@pytest.mark.parametrize("symbol", [None, "MSFT", "", 123])
def test_gate_rejects_missing_or_mismatched_symbol(symbol):
    proposal = {
        "symbol": "AAPL",
        "direction": "long",
        "quantity": "5",
        "entry_price": "100",
        "stop_price": "95",
    }
    portfolio = {"equity": "10000", "cash": "10000", "open_risk": "0", "symbol_exposure": "0"}
    context = {"proposal": proposal, "portfolio": portfolio}
    if symbol is not None:
        context["symbol"] = symbol
    assert risk_gate(context) is False


@pytest.mark.parametrize("direction", [None, "short", "LONG", True])
def test_gate_rejects_missing_or_unsupported_direction(direction):
    proposal = {"symbol": "AAPL", "quantity": "5", "entry_price": "100", "stop_price": "95"}
    if direction is not None:
        proposal["direction"] = direction
    assert proposal_complete(proposal) is False
    assert risk_gate({"symbol": "AAPL", "proposal": proposal, "portfolio": {}}) is False
