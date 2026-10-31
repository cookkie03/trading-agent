"""Guided OHLCV ingestion smoke test for Yahoo Finance and Alpaca."""

from __future__ import annotations

import argparse
import os
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

from data.interface import MarketDataProvider
from data.models import PriceBar as ProviderPriceBar
from data.providers.alpaca_market_data import AlpacaMarketDataProvider
from data.providers.yahoo_finance import YahooFinanceProvider
from storage import PriceBar, SQLiteDatabase


def to_storage_bar(bar: ProviderPriceBar) -> PriceBar:
    """Adapt a provider bar to storage, using its timestamp as the reference date."""
    return PriceBar(
        symbol=bar.symbol,
        interval=bar.interval,
        timestamp=bar.timestamp,
        open=bar.open,
        high=bar.high,
        low=bar.low,
        close=bar.close,
        volume=bar.volume,
        source=bar.source,
        collected_at=bar.collected_at,
        publication_date=bar.publication_date or bar.timestamp,
        reference_date=bar.reference_date or bar.timestamp,
        raw_payload=bar.raw_payload,
    )


def ingest(
    provider: MarketDataProvider,
    database: SQLiteDatabase,
    *,
    symbols: Iterable[str],
    start: datetime,
    end: datetime,
    interval: str = "1d",
) -> dict[str, dict[str, int]]:
    """Fetch and persist bars, returning per-symbol insertion statistics."""
    results: dict[str, dict[str, int]] = {}
    for raw_symbol in symbols:
        symbol = raw_symbol.strip().upper()
        if not symbol:
            raise ValueError("symbols must not contain blanks")
        bars = provider.get_ohlcv_history(symbol, start, end, interval)
        inserted = sum(database.market_data.save(to_storage_bar(bar)) for bar in bars)
        results[symbol] = {
            "fetched": len(bars),
            "inserted": inserted,
            "duplicates": len(bars) - inserted,
        }
    return results


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise argparse.ArgumentTypeError(
            "datetime must include a timezone, e.g. 2026-10-01T00:00:00Z"
        )
    return parsed.astimezone(UTC)


def _provider(name: str) -> MarketDataProvider:
    if name == "yahoo":
        return YahooFinanceProvider()
    api_key = os.environ.get("ALPACA_API_KEY", "")
    secret_key = os.environ.get("ALPACA_SECRET_KEY", "")
    return AlpacaMarketDataProvider.from_env(
        api_key,
        secret_key,
        feed=os.environ.get("ALPACA_DATA_FEED", "iex"),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("yahoo", "alpaca"), default="yahoo")
    parser.add_argument("--symbols", nargs="+", default=("AAPL", "MSFT", "SPY"))
    parser.add_argument("--start", type=_parse_datetime, required=True)
    parser.add_argument("--end", type=_parse_datetime, required=True)
    parser.add_argument("--interval", default="1d")
    parser.add_argument("--database", type=Path, default=Path("data/trading.sqlite"))
    args = parser.parse_args()

    args.database.parent.mkdir(parents=True, exist_ok=True)
    with SQLiteDatabase(args.database) as database:
        results = ingest(
            _provider(args.provider),
            database,
            symbols=args.symbols,
            start=args.start,
            end=args.end,
            interval=args.interval,
        )
        for symbol, stats in results.items():
            print(
                f"{args.provider} {symbol}: fetched={stats['fetched']} "
                f"inserted={stats['inserted']} duplicates={stats['duplicates']}"
            )


if __name__ == "__main__":
    main()
