from datetime import UTC, datetime, timedelta

from agents.graph import Analysis, build_agent_graph


def test_graph_uses_six_agents_and_approves_only_after_risk_gate():
    now = datetime(2026, 11, 5, tzinfo=UTC)
    called = []

    def analyst(role):
        def run(context):
            called.append(role)
            return Analysis(role, now, {"summary": role})

        return run

    def pm(context):
        called.append("portfolio_manager")
        assert set(context["analyses"]) == {
            "market",
            "sentiment",
            "technical",
            "fundamental",
            "risk",
        }
        return {"decision": "approve"}

    graph = build_agent_graph(
        analysts={
            role: analyst(role)
            for role in ("market", "sentiment", "technical", "fundamental", "risk")
        },
        portfolio_manager=pm,
        risk_gate=lambda context: True,
        proposal_complete=lambda proposal: True,
        max_age=timedelta(hours=1),
    )
    result = graph.invoke({"context": {}, "now": now})
    assert result["decision"] == "approved"
    assert set(called) == {
        "market",
        "sentiment",
        "technical",
        "fundamental",
        "risk",
        "portfolio_manager",
    }


def test_stale_analysis_never_reaches_pm_or_risk_gate():
    now = datetime(2026, 11, 5, tzinfo=UTC)
    roles = ("market", "sentiment", "technical", "fundamental", "risk")
    graph = build_agent_graph(
        analysts={
            role: lambda context, role=role: Analysis(
                role, now - timedelta(hours=2), {"summary": "old"}
            )
            for role in roles
        },
        portfolio_manager=lambda context: (_ for _ in ()).throw(AssertionError("PM called")),
        risk_gate=lambda context: (_ for _ in ()).throw(AssertionError("gate called")),
        proposal_complete=lambda proposal: True,
        max_age=timedelta(hours=1),
    )
    assert graph.invoke({"context": {}, "now": now})["decision"] == "pending"


def test_risk_veto_cannot_be_overridden_by_pm():
    now = datetime(2026, 11, 5, tzinfo=UTC)
    roles = ("market", "sentiment", "technical", "fundamental", "risk")
    graph = build_agent_graph(
        analysts={
            role: lambda context, role=role: Analysis(role, now, {"summary": "ok"})
            for role in roles
        },
        portfolio_manager=lambda context: {"decision": "approve"},
        risk_gate=lambda context: False,
        proposal_complete=lambda proposal: True,
        max_age=timedelta(hours=1),
    )
    assert graph.invoke({"context": {}, "now": now})["decision"] == "rejected"


def test_pm_cannot_change_context_seen_by_risk_gate():
    now = datetime(2026, 11, 5, tzinfo=UTC)
    roles = ("market", "sentiment", "technical", "fundamental", "risk")

    def pm(context):
        context["portfolio"]["cash"] = 999
        return {"decision": "approve"}

    graph = build_agent_graph(
        analysts={
            role: lambda context, role=role: Analysis(role, now, {"summary": "ok"})
            for role in roles
        },
        portfolio_manager=pm,
        risk_gate=lambda context: context["portfolio"]["cash"] == 999,
        proposal_complete=lambda proposal: True,
        max_age=timedelta(hours=1),
    )
    result = graph.invoke({"context": {"portfolio": {"cash": 0}}, "now": now})
    assert result["decision"] == "rejected"


def test_analysis_expiring_during_pm_becomes_pending():
    now = datetime(2026, 11, 5, tzinfo=UTC)
    times = iter((now, now + timedelta(hours=2)))
    roles = ("market", "sentiment", "technical", "fundamental", "risk")
    graph = build_agent_graph(
        analysts={
            role: lambda context, role=role: Analysis(role, now, {"summary": "ok"})
            for role in roles
        },
        portfolio_manager=lambda context: {"decision": "approve"},
        risk_gate=lambda context: True,
        proposal_complete=lambda proposal: True,
        max_age=timedelta(hours=1),
        clock=lambda: next(times),
    )
    assert graph.invoke({"context": {}})["decision"] == "pending"
