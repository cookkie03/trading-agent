"""Current Yahoo fundamentals with explicit observation time, not point-in-time history."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

import yfinance as yf


@dataclass(frozen=True)
class FundamentalObservation:
    symbol: str
    metric: str
    value: Decimal
    source: str
    observed_at: datetime


class YahooFundamentalsProvider:
    def __init__(self, ticker_factory=yf.Ticker, clock=lambda: datetime.now(UTC)):
        self._ticker_factory = ticker_factory
        self._clock = clock

    def get_fundamentals(self, symbol: str) -> tuple[FundamentalObservation, ...]:
        symbol = symbol.strip().upper()
        if not symbol:
            raise ValueError("symbol must not be blank")
        info = self._ticker_factory(symbol).info
        observed_at = self._clock()
        if observed_at.utcoffset() is None:
            raise ValueError("observation time must be timezone-aware")
        value = info.get("marketCap")
        if value is None or isinstance(value, bool):
            return ()
        try:
            market_cap = Decimal(str(value))
        except InvalidOperation as error:
            raise ValueError("invalid market capitalization") from error
        if not market_cap.is_finite() or market_cap <= 0:
            raise ValueError("invalid market capitalization")
        return (
            FundamentalObservation(symbol, "market_cap", market_cap, "yahoo:yfinance", observed_at),
        )
