"""Adapter Yahoo Finance per storico OHLCV."""

from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import yfinance as yf

from ..models import PriceBar


class YahooFinanceProvider:
    """Normalizza `yfinance.Ticker.history` nel contratto interno."""

    def __init__(
        self,
        ticker_factory: Callable[[str], Any] = yf.Ticker,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._ticker_factory = ticker_factory
        self._clock = clock

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
        _require_aware_utc(start, "start")
        _require_aware_utc(end, "end")
        if start >= end:
            raise ValueError("start must be earlier than end")

        history = self._ticker_factory(symbol).history(
            start=start,
            end=end,
            interval=interval,
            auto_adjust=False,
            actions=False,
        )
        required_columns = {"Open", "High", "Low", "Close", "Volume"}
        if not required_columns.issubset(history.columns):
            missing = ", ".join(sorted(required_columns - set(history.columns)))
            raise ValueError(f"Yahoo Finance response is missing columns: {missing}")

        collected_at = self._clock()
        _require_aware_utc(collected_at, "clock result")
        return tuple(
            PriceBar(
                symbol=symbol,
                interval=interval,
                timestamp=_as_utc(row_index),
                open=Decimal(str(row["Open"])),
                high=Decimal(str(row["High"])),
                low=Decimal(str(row["Low"])),
                close=Decimal(str(row["Close"])),
                volume=Decimal(str(row["Volume"])),
                source="yahoo_finance",
                collected_at=collected_at,
            )
            for row_index, row in history.iterrows()
        )


def _as_utc(value: Any) -> datetime:
    timestamp = value.to_pydatetime() if hasattr(value, "to_pydatetime") else value
    if not isinstance(timestamp, datetime):
        raise ValueError("Yahoo Finance returned a non-datetime index")
    _require_aware_utc(timestamp, "bar timestamp")
    return timestamp.astimezone(UTC)


def _require_aware_utc(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must include a timezone")
