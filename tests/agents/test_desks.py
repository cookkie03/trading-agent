from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal

from agents.desks import (
    DeskContext,
    FundamentalAnalyst,
    MarketAnalyst,
    SentimentAnalyst,
    TechnicalAnalyst,
    run_desks,
)
from data.models import PriceBar
from data.providers.alpaca_news import NewsItem
from data.providers.yahoo_fundamentals import FundamentalObservation
from tests.workflows.test_trade_cycle import approved_state


def test_specialists_can_be_invoked_independently_with_missing_evidence():
    state = approved_state()
    context = DeskContext(state.symbol, date(2026, 11, 2), Decimal("100"), state)

    market = MarketAnalyst().analyze(context)
    assert market.desk == "market"
    assert market.view == "market context pending provider evidence"
    assert market.evidence == ()
    assert SentimentAnalyst().analyze(context).view == "sentiment context pending provider evidence"
    assert SentimentAnalyst().analyze(context).evidence == ()
    assert (
        FundamentalAnalyst().analyze(context).view
        == "fundamentals context pending provider evidence"
    )
    assert FundamentalAnalyst().analyze(context).evidence == ()
    technical = TechnicalAnalyst().analyze(context)
    assert technical.view == state.technical_view
    assert technical.evidence == (
        "atr | sqlite:price_bars | atr-wilder-v1 | 2026-11-02T14:00:00+00:00",
    )


def test_specialists_preserve_observations_and_provenance():
    state = approved_state()
    now = datetime(2026, 11, 2, 14, tzinfo=UTC)
    price = Decimal("100")
    context = DeskContext(
        state.symbol,
        now.date(),
        price,
        state,
        news=(NewsItem("Earnings announced", "wire", "https://example.com/news", now),),
        fundamentals=(
            FundamentalObservation(state.symbol, "market_cap", Decimal("500"), "yahoo", now),
        ),
        market_bar=PriceBar(
            "SPY", "1d", now, price, price, price, price, Decimal("10"), "feed", now
        ),
    )
    market = MarketAnalyst().analyze(context)
    assert market.view == "SPY close 100"
    assert market.evidence == ("feed | 2026-11-02T14:00:00+00:00",)
    sentiment = SentimentAnalyst().analyze(context)
    assert sentiment.view == "Earnings announced"
    assert sentiment.evidence == ("wire | 2026-11-02T14:00:00+00:00 | https://example.com/news",)
    fundamental = FundamentalAnalyst().analyze(context)
    assert fundamental.view == "market_cap: 500"
    assert fundamental.evidence == ("yahoo | observed 2026-11-02T14:00:00+00:00",)
    assert run_desks(context) == tuple(
        analyst.analyze(context)
        for analyst in (
            MarketAnalyst(),
            TechnicalAnalyst(),
            FundamentalAnalyst(),
            SentimentAnalyst(),
        )
    )
    assert TechnicalAnalyst().analyze(
        replace(context, news=(), fundamentals=(), market_bar=None)
    ) == TechnicalAnalyst().analyze(context)


def test_all_required_desks_return_named_contributions():
    state = approved_state()
    opinions = run_desks(
        DeskContext(
            symbol=state.symbol,
            as_of=date(2026, 11, 2),
            current_price=Decimal("100"),
            research=state,
        )
    )

    assert {opinion.desk for opinion in opinions} == {
        "market",
        "technical",
        "fundamentals",
        "sentiment",
    }
    assert all(opinion.view and opinion.rationale for opinion in opinions)
    assert opinions[1].evidence == (
        "atr | sqlite:price_bars | atr-wilder-v1 | 2026-11-02T14:00:00+00:00",
    )
