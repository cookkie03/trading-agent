"""Modelli di dati indipendenti dal provider."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class PriceBar:
    """Una barra OHLCV normalizzata, con timestamp in UTC."""

    symbol: str
    interval: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    source: str
    collected_at: datetime
    publication_date: datetime | None = None
    reference_date: datetime | None = None
    raw_payload: str = "{}"
