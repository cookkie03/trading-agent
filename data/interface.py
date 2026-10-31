"""Contratto interno per provider di dati di mercato."""

from datetime import datetime
from typing import Protocol

from .models import PriceBar


class MarketDataProvider(Protocol):
    def get_ohlcv_history(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str = "1d",
    ) -> tuple[PriceBar, ...]:
        """Restituisce barre OHLCV con inizio incluso e fine esclusa."""
        ...
