"""Small idempotent seam between approved intents and a paper gateway."""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Protocol

from .risk import RiskDecision


@dataclass(frozen=True)
class OrderRequest:
    client_order_id: str
    symbol: str
    quantity: Decimal
    limit_price: Decimal
    take_profit_price: Decimal
    stop_price: Decimal

    def __post_init__(self) -> None:
        if not self.client_order_id.strip() or not self.symbol.strip():
            raise ValueError("order identity must not be empty")
        if min(self.quantity, self.limit_price, self.stop_price) <= 0:
            raise ValueError("order values must be positive")
        if self.stop_price >= self.limit_price:
            raise ValueError("stop_price must be below limit_price")
        if self.take_profit_price <= self.limit_price:
            raise ValueError("take_profit_price must be above limit_price")

    def different(self, **changes: object) -> OrderRequest:
        return replace(self, **changes)


@dataclass(frozen=True)
class Submission:
    client_order_id: str
    broker_order_id: str


class PaperGateway(Protocol):
    def submit(self, request: OrderRequest) -> Submission:
        ...

    def find_by_client_order_id(self, client_order_id: str) -> Submission:
        ...


class IdempotentPaperExecutor:
    """Submit only risk-approved orders and remember client IDs."""

    def __init__(self, gateway: PaperGateway, orders=None) -> None:
        self._gateway = gateway
        self._orders = orders
        self._requests: dict[str, OrderRequest] = {}
        self._audit: list[Submission] = []

    @property
    def audit_log(self) -> tuple[Submission, ...]:
        return tuple(self._audit)

    def submit(self, request: OrderRequest, decision: RiskDecision) -> Submission:
        if not decision.approved:
            raise ValueError(f"risk gate rejected order: {', '.join(decision.reasons)}")
        if request.quantity > decision.quantity:
            raise ValueError("order quantity exceeds risk-approved quantity")
        previous = self._requests.get(request.client_order_id)
        if previous is not None:
            if previous != request:
                raise ValueError("client order ID was used for a different order")
            return self._submission_for(request.client_order_id)
        if self._orders is not None:
            created, broker_order_id = self._orders.reserve(request)
            if not created:
                if broker_order_id is None:
                    raise RuntimeError("paper order requires broker reconciliation before retry")
                return Submission(request.client_order_id, broker_order_id)
        submission = self._gateway.submit(request)
        if self._orders is not None:
            self._orders.complete(request.client_order_id, submission.broker_order_id)
        self._requests[request.client_order_id] = request
        self._audit.append(submission)
        return submission

    def reconcile(self, request: OrderRequest) -> Submission:
        if self._orders is None:
            raise RuntimeError("reconciliation requires persistent order reservations")
        broker_id = self._orders.existing(request)
        if broker_id is not None:
            return Submission(request.client_order_id, broker_id)
        submission = self._gateway.find_by_client_order_id(request.client_order_id)
        if submission.client_order_id != request.client_order_id or not submission.broker_order_id:
            raise ValueError("broker returned an invalid order identity")
        self._orders.complete(request.client_order_id, submission.broker_order_id)
        return Submission(submission.client_order_id, submission.broker_order_id)

    def _submission_for(self, client_order_id: str) -> Submission:
        return next(item for item in self._audit if item.client_order_id == client_order_id)
