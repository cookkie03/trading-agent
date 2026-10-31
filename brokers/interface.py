"""Contratto piccolo, implementabile anche da broker futuri o fake offline."""

from typing import Protocol

from .models import Account, Order, OrderQuery, Position


class Broker(Protocol):
    def get_account(self) -> Account:
        """Restituisce il conto normalizzato.

        Un errore di lettura resta un errore: non equivale a un conto vuoto o
        a un saldo pari a zero.
        """
        ...

    def get_positions(self) -> tuple[Position, ...]:
        """Restituisce le posizioni aperte osservate dal broker.

        Short e asset non-equity restano nel risultato; la policy che decide
        quali strumenti siano ammessi appartiene alla strategia, non all'adapter.
        """
        ...

    def get_orders(self, query: OrderQuery | None = None) -> tuple[Order, ...]:
        """Restituisce una finestra limitata dal più recente.

        Le gambe degli ordini restano annidate e gli errori del broker non
        vengono trasformati in una sequenza vuota.
        """
        ...
