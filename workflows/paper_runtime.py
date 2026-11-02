"""Compose the paper order cycle with durable local repositories."""

from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta

from alpaca.trading.client import TradingClient

from analysis.indicators import average_true_range
from analysis.strategy_state import QuantitativeEvaluation
from brokers.alpaca_orders import AlpacaPaperOrders
from config import Settings
from data.ingestion import ingest_ohlcv
from execution.paper import IdempotentPaperExecutor
from storage.sqlite import DecisionRecord
from workflows.langgraph_workflow import build_research_graph
from workflows.market_calendar import alpaca_daily_timestamps, alpaca_hourly_timestamps
from workflows.trade_cycle import TradeCycle


def paper_runtime(client, database):
    """Compose an injected client, allowing deterministic offline tests."""
    executor = IdempotentPaperExecutor(AlpacaPaperOrders(client), database.paper_orders)
    return TradeCycle(executor, database.decisions), executor


def run_research_cycle(client, database, state, portfolio, limits, entry_price, *, news=()):
    """Run research and only execute a decision approved by the complete graph."""
    result = build_research_graph().invoke(
        {
            "research": state,
            "portfolio": asdict(portfolio),
            "limits": asdict(limits),
            "entry_price": entry_price,
            "news": news,
        }
    )
    if result["decision"] == "approved":
        cycle, _ = paper_runtime(client, database)
        result["execution"] = cycle.run(result["risk_review"].state, portfolio, limits, entry_price)
    else:
        review = result["risk_review"]
        rationale = (
            "; ".join(review.decision.reasons)
            if result["decision"] == "rejected"
            else "Desk evidence or technical review incomplete"
        )
        database.decisions.save(
            DecisionRecord(
                client_order_id=f"{state.run_id}:{state.symbol}:research:{result['decision']}",
                symbol=state.symbol,
                status=result["decision"],
                direction=state.proposed_direction,
                conviction=state.conviction,
                rationale=rationale,
                observed_at=datetime.now(UTC),
                payload=state.run_id,
            )
        )
    return result


def run_provider_research_cycle(
    provider,
    client,
    database,
    state,
    portfolio,
    limits,
    *,
    start,
    end,
    interval,
    as_of: datetime,
    max_age: timedelta,
    expected_timestamps: tuple[datetime, ...] | None = None,
    calendar_client=None,
    news_provider=None,
):
    """Ingest provider bars and attach their latest close to technical research."""
    if as_of.utcoffset() is None or max_age <= timedelta(0):
        raise ValueError("as_of must be timezone-aware and max_age must be positive")
    if end > as_of:
        raise ValueError("market data interval cannot extend beyond as_of")
    ingest_ohlcv(provider, database, symbol=state.symbol, start=start, end=end, interval=interval)
    bars = database.market_data.list_between(state.symbol, interval, start, end)
    if not bars:
        raise ValueError("no market bar available in requested interval")
    if expected_timestamps is None:
        calendars = {"1d": alpaca_daily_timestamps, "1h": alpaca_hourly_timestamps}
        if calendar_client is None or interval not in calendars:
            raise ValueError("Alpaca calendar or explicit expected timestamps required")
        expected_timestamps = calendars[interval](calendar_client, start, end)
    if not expected_timestamps or any(
        timestamp.utcoffset() is None or not start <= timestamp < end
        for timestamp in expected_timestamps
    ):
        raise ValueError("expected market timestamps must be timezone-aware and in range")
    if set(expected_timestamps) - {bar.timestamp for bar in bars}:
        raise ValueError("missing market bars in expected schedule")
    if len({bar.source for bar in bars}) != 1 or len({bar.timestamp for bar in bars}) != len(bars):
        raise ValueError("ATR requires a single unambiguous market data source")
    atr_values = average_true_range(
        [bar.high for bar in bars],
        [bar.low for bar in bars],
        [bar.close for bar in bars],
        window=14,
    )
    if not atr_values:
        raise ValueError("ATR requires at least 15 bars")
    bar = bars[-1]
    if as_of - bar.timestamp > max_age:
        raise ValueError("market data is stale")
    evaluation = QuantitativeEvaluation(
        name="atr",
        values={"atr": atr_values[-1]},
        observed_at=bar.timestamp,
        source=bar.source,
        parameters={"window": 14, "interval": interval},
        formula_version="atr-wilder-v1",
        interpretation="Wilder ATR from provider bars",
    )
    state = replace(
        state,
        evaluations=tuple(item for item in state.evaluations if "atr" not in item.values)
        + (evaluation,),
        technical_view=(
            f"{state.technical_view} Latest {interval} close {bar.close} "
            f"at {bar.timestamp.isoformat()} from {bar.source}."
        ),
    )
    news = news_provider.get_news(state.symbol, start, end) if news_provider else ()
    return run_research_cycle(client, database, state, portfolio, limits, bar.close, news=news)


def alpaca_paper_runtime(settings: Settings, database):
    """Construct the SDK client with its fixed paper endpoint, never a URL override."""
    if settings.alpaca_trading_url.rstrip("/") != "https://paper-api.alpaca.markets/v2":
        raise ValueError("paper runtime requires the Alpaca paper endpoint")
    if not settings.alpaca_api_key or not settings.alpaca_secret_key:
        raise ValueError("Alpaca paper credentials are required")
    client = TradingClient(
        settings.alpaca_api_key.get_secret_value(),
        settings.alpaca_secret_key.get_secret_value(),
        paper=True,
    )
    return paper_runtime(client, database)
