"""Dati pubblici del broker: nessuna dipendenza dall'SDK di un fornitore."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal


@dataclass(frozen=True)
class Account:
    """Cash è liquidità; buying_power può includere margine e non è cash."""

    id: str
    status: str
    currency: str
    cash: Decimal
    equity: Decimal
    buying_power: Decimal
    trading_blocked: bool


@dataclass(frozen=True)
class Position:
    symbol: str
    asset_class: str
    side: str
    quantity: Decimal
    quantity_available: Decimal | None
    average_entry_price: Decimal
    current_price: Decimal | None
    market_value: Decimal | None
    unrealized_profit_loss: Decimal | None


@dataclass(frozen=True)
class OrderQuery:
    """Una finestra limitata, non uno storico completo. Estremi temporali esclusivi."""

    status: Literal["open", "closed", "all"] = "open"
    symbols: tuple[str, ...] = ()
    limit: int = 100
    after: datetime | None = None
    until: datetime | None = None

    def __post_init__(self) -> None:
        if self.status not in ("open", "closed", "all"):
            raise ValueError("status must be open, closed or all")
        if type(self.limit) is not int or not 1 <= self.limit <= 500:
            raise ValueError("limit must be an integer between 1 and 500")
        if not isinstance(self.symbols, tuple) or any(
            not isinstance(s, str) or not s.strip() or s != s.strip() for s in self.symbols
        ):
            raise ValueError("symbols must be a tuple of non-blank symbols")
        for value in (self.after, self.until):
            if value is not None and (value.tzinfo is None or value.utcoffset() is None):
                raise ValueError("order query dates must include a timezone")
        if self.after is not None and self.until is not None and self.after >= self.until:
            raise ValueError("after must precede until")


@dataclass(frozen=True)
class Order:
    id: str
    client_order_id: str
    symbol: str | None
    asset_class: str | None
    side: str | None
    order_type: str | None
    status: str
    quantity: Decimal | None
    notional: Decimal | None
    filled_quantity: Decimal
    limit_price: Decimal | None
    stop_price: Decimal | None
    average_fill_price: Decimal | None
    submitted_at: datetime | None
    filled_at: datetime | None
    legs: tuple["Order", ...] = ()


ErrorKind = Literal[
    "authentication", "rate_limit", "unavailable", "invalid_request", "invalid_response"
]


class BrokerError(Exception):
    """Errore controllabile dal chiamante, senza tipi o credenziali del vendor."""

    def __init__(
        self, kind: ErrorKind, *, status_code: int | None = None, broker_code: str | None = None
    ) -> None:
        self.kind = kind
        self.status_code = status_code
        self.broker_code = broker_code
        super().__init__(f"Broker read failed: {kind}")
