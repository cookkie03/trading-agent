"""Contratto piccolo, implementabile anche da broker futuri o fake offline."""

from typing import Protocol

from .models import Account, Order, OrderQuery, Position


class Broker(Protocol):
    def get_account(self) -> Account:
        """Legge il conto dal broker; gli errori non sono risultati vuoti."""
        ...

    def get_positions(self) -> tuple[Position, ...]:
        """Legge le posizioni aperte; conserva anche short e asset non equity."""
        ...

    def get_orders(self, query: OrderQuery | None = None) -> tuple[Order, ...]:
        """Legge al massimo query.limit ordini, dal più recente, con gambe annidate."""
        ...
