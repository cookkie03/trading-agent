"""Compose the paper order cycle with durable local repositories."""

from alpaca.trading.client import TradingClient

from brokers.alpaca_orders import AlpacaPaperOrders
from config import Settings
from execution.paper import IdempotentPaperExecutor
from workflows.trade_cycle import TradeCycle


def paper_runtime(client, database):
    """Compose an injected client, allowing deterministic offline tests."""
    executor = IdempotentPaperExecutor(AlpacaPaperOrders(client), database.paper_orders)
    return TradeCycle(executor, database.decisions), executor


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
