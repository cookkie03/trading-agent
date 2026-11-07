from datetime import UTC, datetime, timedelta

from agents.desks import DeskOpinion
from agents.graph import Analysis, build_agent_graph
from agents.portfolio_manager import PortfolioManager, PortfolioResult
from agents.portfolio_manager_adapter import portfolio_manager_adapter


def test_graph_preserves_evidence_and_never_approves_proposal():
    now = datetime(2026, 11, 5, tzinfo=UTC)
    received = []

    def backend(request):
        received.append(request)
        return PortfolioResult("propose", "buy", "medium", "thesis", ())

    roles = ("market", "sentiment", "technical", "fundamental", "risk")
    graph = build_agent_graph(
        analysts={
            role: lambda _, role=role: Analysis(role, now, {"evidence": ["source-123"]})
            for role in roles
        },
        portfolio_manager=portfolio_manager_adapter(PortfolioManager(backend)),
        risk_gate=lambda _: (_ for _ in ()).throw(AssertionError("must not approve")),
        proposal_complete=lambda _: True,
        max_age=timedelta(hours=1),
    )
    result = graph.invoke({"context": {"symbol": "AAPL", "portfolio_context": "cash"}, "now": now})
    assert result["decision"] == "pending"
    assert result["proposal"]["direction"] == "buy"
    assert result["proposal"]["pm_decision"] == "propose"
    assert "source-123" in received[0].analyses["market"]
    assert now.isoformat() in received[0].analyses["market"]


def test_adapter_missing_context_abstains():
    pm = portfolio_manager_adapter(PortfolioManager(lambda _: None))
    result = pm({"analyses": {}})
    assert result["decision"] == "pending"
    assert result["pm_decision"] == "abstain"
    assert "symbol" in result["missing_data"]
    assert "portfolio_context" in result["missing_data"]


def test_desk_opinion_without_evidence_is_missing():
    now = datetime(2026, 11, 5, tzinfo=UTC)
    roles = ("market", "sentiment", "technical", "fundamental", "risk")
    analyses = {role: Analysis(role, now, {"summary": "available"}) for role in roles}
    analyses["market"] = Analysis(
        "market", now, {"opinion": DeskOpinion("market", "pending", "no data", ())}
    )

    def backend(_):
        raise AssertionError("backend called without evidence")

    result = portfolio_manager_adapter(PortfolioManager(backend))(
        {
            "symbol": "AAPL",
            "portfolio_context": "cash",
            "analyses": analyses,
        }
    )
    assert result["decision"] == "pending"
    assert result["pm_decision"] == "abstain"
    assert "market" in result["missing_data"]
