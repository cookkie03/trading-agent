from agents.portfolio_manager import PortfolioManager, PortfolioRequest, PortfolioResult


def test_missing_data_abstains_without_calling_backend():
    def backend(request):
        raise AssertionError("backend must not be called")

    result = PortfolioManager(backend).evaluate(PortfolioRequest("AAPL", {}, ""))

    assert result.decision == "abstain"
    assert "portfolio_context" in result.missing_data
    assert "market" in result.missing_data


def test_complete_input_returns_backend_proposal():
    request = PortfolioRequest(
        "AAPL",
        {
            role: f"{role} evidence"
            for role in ("market", "sentiment", "technical", "fundamental", "risk")
        },
        "cash and positions available",
    )
    proposal = PortfolioResult("propose", "buy", "medium", "balanced thesis", ())
    assert (
        PortfolioManager(lambda received: proposal if received == request else None).evaluate(
            request
        )
        == proposal
    )


def test_backend_uncertainty_or_failure_abstains():
    request = PortfolioRequest(
        "AAPL",
        {role: "evidence" for role in ("market", "sentiment", "technical", "fundamental", "risk")},
        "portfolio",
    )
    result = PortfolioManager(
        lambda _: PortfolioResult("propose", "buy", "medium", "", ("valuation",))
    ).evaluate(request)
    assert result.decision == "abstain"
    assert "valuation" in result.missing_data

    def broken(_):
        raise RuntimeError("unavailable")

    assert PortfolioManager(broken).evaluate(request).decision == "abstain"
