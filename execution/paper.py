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
    stop_price: Decimal

    def __post_init__(self) -> None:
        if not self.client_order_id.strip() or not self.symbol.strip():
            raise ValueError("order identity must not be empty")
        if min(self.quantity, self.limit_price, self.stop_price) <= 0:
            raise ValueError("order values must be positive")
        if self.stop_price >= self.limit_price:
            raise ValueError("stop_price must be below limit_price")

    def different(self, **changes: object) -> OrderRequest:
        return replace(self, **changes)


@dataclass(frozen=True)
class Submission:
    client_order_id: str
    broker_order_id: str


class PaperGateway(Protocol):
    def submit(self, request: OrderRequest) -> Submission:
        ...


class IdempotentPaperExecutor:
    """Submit only risk-approved orders and remember client IDs."""

    def __init__(self, gateway: PaperGateway) -> None:
        self._gateway = gateway
        self._requests: dict[str, OrderRequest] = {}
        self._audit: list[Submission] = []

    @property
    def audit_log(self) -> tuple[Submission, ...]:
        return tuple(self._audit)

    def submit(self, request: OrderRequest, decision: RiskDecision) -> Submission:
        if not decision.approved:
            raise ValueError(f"risk gate rejected order: {', '.join(decision.reasons)}")
        previous = self._requests.get(request.client_order_id)
        if previous is not None:
            if previous != request:
                raise ValueError("client order ID was used for a different order")
            return self._submission_for(request.client_order_id)
        submission = self._gateway.submit(request)
        self._requests[request.client_order_id] = request
        self._audit.append(submission)
        return submission

    def _submission_for(self, client_order_id: str) -> Submission:
        return next(item for item in self._audit if item.client_order_id == client_order_id)
