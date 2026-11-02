"""Write-only Alpaca paper-order adapter with a local normalized seam."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import LimitOrderRequest, StopLossRequest, TakeProfitRequest


@dataclass(frozen=True)
class PaperOrderRequest:
    client_order_id: str
    symbol: str
    quantity: Decimal
    limit_price: Decimal
    take_profit_price: Decimal
    stop_price: Decimal


@dataclass(frozen=True)
class PaperSubmission:
    broker_order_id: str
    client_order_id: str


class TradingClientLike(Protocol):
    def submit_order(self, request): ...
    def cancel_order_by_id(self, order_id): ...
    def get_order_by_client_id(self, client_order_id): ...


class AlpacaPaperOrders:
    def __init__(self, client: TradingClientLike) -> None:
        self._client = client

    def submit(self, order: PaperOrderRequest) -> PaperSubmission:
        request = LimitOrderRequest(
            symbol=order.symbol,
            qty=str(order.quantity),
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
            limit_price=str(order.limit_price),
            order_class="bracket",
            take_profit=TakeProfitRequest(limit_price=float(order.take_profit_price)),
            stop_loss=StopLossRequest(stop_price=str(order.stop_price)),
            client_order_id=order.client_order_id,
        )
        result = self._client.submit_order(request)
        return PaperSubmission(
            broker_order_id=str(result.id),
            client_order_id=str(result.client_order_id),
        )

    def find_by_client_order_id(self, client_order_id: str) -> PaperSubmission:
        if not client_order_id.strip():
            raise ValueError("client_order_id must not be empty")
        result = self._client.get_order_by_client_id(client_order_id)
        return PaperSubmission(
            broker_order_id=str(result.id), client_order_id=str(result.client_order_id)
        )

    def cancel(self, broker_order_id: str) -> None:
        if not broker_order_id.strip():
            raise ValueError("broker_order_id must not be empty")
        self._client.cancel_order_by_id(broker_order_id)
