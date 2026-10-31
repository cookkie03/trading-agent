"""Modelli di dati indipendenti dal provider."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class MacroObservation:
    """Serie macroeconomica normalizzata, con valori datati in UTC."""

    series: str
    observations: tuple[tuple[datetime, Decimal], ...]
    source: str
    collected_at: datetime


@dataclass(frozen=True)
class FundamentalMetrics:
    """Metriche fondamentali normalizzate per un simbolo."""

    symbol: str
    values: dict[str, Decimal | None]
    source: str
    collected_at: datetime


@dataclass(frozen=True)
class PriceBar:
    """Barra OHLCV normalizzata, con timestamp e raccolta in UTC.

    I valori numerici restano ``Decimal`` per evitare che la conversione a
    ``float`` introduca perdita di precisione prima dei calcoli finanziari.
    ``source`` e ``raw_payload`` conservano la provenienza necessaria alla
    verifica e alla deduplicazione delle osservazioni.
    """

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
