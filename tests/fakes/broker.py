"""Conto deterministico vuoto: utile per sviluppare senza credenziali o rete."""

from dataclasses import dataclass

from trading_agent.brokers.models import Account, Order, OrderQuery, Position


@dataclass(frozen=True)
class EmptyBroker:
    account: Account

    def get_account(self) -> Account:
        return self.account

    def get_positions(self) -> tuple[Position, ...]:
        return ()

    def get_orders(self, query: OrderQuery | None = None) -> tuple[Order, ...]:
        return ()
