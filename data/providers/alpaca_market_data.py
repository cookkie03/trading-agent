"""Adapter Alpaca Market Data verso il contratto interno."""

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from alpaca.data.enums import DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

from ..models import PriceBar

_INTERVALS: dict[str, TimeFrame] = {
    "1m": TimeFrame(1, TimeFrameUnit.Minute),
    "5m": TimeFrame(5, TimeFrameUnit.Minute),
    "15m": TimeFrame(15, TimeFrameUnit.Minute),
    "1h": TimeFrame(1, TimeFrameUnit.Hour),
    "1d": TimeFrame.Day,
}


class AlpacaMarketDataProvider:
    """Normalizza barre equities storiche con feed e provenienza espliciti.

    L'SDK resta confinato all'adapter: il resto del sistema riceve solo
    ``PriceBar`` e non deve conoscere i tipi Alpaca.
    """

    def __init__(
        self,
        client: StockHistoricalDataClient,
        feed: str,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._client = client
        self._feed = _parse_feed(feed)
        self._clock = clock

    @classmethod
    def from_env(
        cls,
        api_key: str,
        secret_key: str,
        feed: str = "iex",
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> "AlpacaMarketDataProvider":
        if not api_key.strip() or not secret_key.strip():
            raise ValueError("Both Alpaca market data credentials are required")
        return cls(StockHistoricalDataClient(api_key, secret_key), feed, clock)

    def get_ohlcv_history(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str = "1d",
    ) -> tuple[PriceBar, ...]:
        symbol = symbol.strip().upper()
        if not symbol:
            raise ValueError("symbol must not be blank")
        _require_aware(start, "start")
        _require_aware(end, "end")
        if start >= end:
            raise ValueError("start must be earlier than end")
        try:
            timeframe = _INTERVALS[interval]
        except KeyError as error:
            raise ValueError(f"Unsupported Alpaca interval: {interval}") from error

        response = self._client.get_stock_bars(
            StockBarsRequest(
                symbol_or_symbols=symbol,
                start=start,
                end=end,
                timeframe=timeframe,
                feed=self._feed,
            )
        )
        collected_at = self._clock()
        _require_aware(collected_at, "clock result")
        rows = response.data.get(symbol, [])
        return tuple(_bar(symbol, interval, row, self._feed.value, collected_at) for row in rows)


def _parse_feed(feed: str) -> DataFeed:
    try:
        return DataFeed(feed.strip().lower())
    except ValueError as error:
        allowed = ", ".join(item.value for item in DataFeed)
        raise ValueError(f"Unsupported Alpaca feed: {feed}; expected one of {allowed}") from error


def _bar(
    symbol: str,
    interval: str,
    row: Mapping[str, Any],
    feed: str,
    collected_at: datetime,
) -> PriceBar:
    timestamp = _as_utc(row["timestamp"])
    return PriceBar(
        symbol=symbol,
        interval=interval,
        timestamp=timestamp,
        open=Decimal(str(row["open"])),
        high=Decimal(str(row["high"])),
        low=Decimal(str(row["low"])),
        close=Decimal(str(row["close"])),
        volume=Decimal(str(row["volume"])),
        source=f"alpaca:{feed}",
        collected_at=collected_at,
        reference_date=timestamp,
    )


def _as_utc(value: Any) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("Alpaca response timestamps must be datetime values")
    if value.tzinfo and value.utcoffset():
        return value.astimezone(UTC)
    return value.replace(tzinfo=UTC)


def _require_aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
