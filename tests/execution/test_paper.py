from decimal import Decimal

import pytest

from execution.paper import IdempotentPaperExecutor, OrderRequest, Submission
from execution.risk import RiskDecision


class FakePaperGateway:
    def __init__(self) -> None:
        self.requests: list[OrderRequest] = []

    def submit(self, request: OrderRequest) -> Submission:
        self.requests.append(request)
        return Submission(client_order_id=request.client_order_id, broker_order_id="paper-1")


def approved() -> RiskDecision:
    return RiskDecision(approved=True, quantity=Decimal("10"), reasons=())


def request(client_order_id="run-1:AAPL") -> OrderRequest:
    return OrderRequest(
        client_order_id=client_order_id,
        symbol="AAPL",
        quantity=Decimal("10"),
        limit_price=Decimal("100"),
        take_profit_price=Decimal("110"),
        stop_price=Decimal("95"),
    )


def test_submission_is_rejected_inside_database_transaction(tmp_path):
    from storage.sqlite import SQLiteDatabase

    gateway = FakePaperGateway()
    with SQLiteDatabase(tmp_path / "orders.db") as db:
        with db.transaction(), pytest.raises(RuntimeError, match="transaction"):
            IdempotentPaperExecutor(gateway, db.paper_orders).submit(request(), approved())
    assert gateway.requests == []


def test_uncertain_submission_is_not_retried_after_restart(tmp_path):
    from storage.sqlite import SQLiteDatabase

    class UncertainGateway(FakePaperGateway):
        def submit(self, request):
            self.requests.append(request)
            raise TimeoutError("broker response lost")

    gateway = UncertainGateway()
    path = tmp_path / "orders.db"
    with SQLiteDatabase(path) as db:
        with pytest.raises(TimeoutError):
            IdempotentPaperExecutor(gateway, db.paper_orders).submit(request(), approved())
    with SQLiteDatabase(path) as db:
        with pytest.raises(RuntimeError, match="reconciliation"):
            IdempotentPaperExecutor(gateway, db.paper_orders).submit(request(), approved())
    assert len(gateway.requests) == 1


def test_submitted_order_is_not_sent_again_after_restart(tmp_path):
    from storage.sqlite import SQLiteDatabase

    gateway = FakePaperGateway()
    path = tmp_path / "orders.db"
    with SQLiteDatabase(path) as db:
        first = IdempotentPaperExecutor(gateway, db.paper_orders).submit(request(), approved())
    with SQLiteDatabase(path) as db:
        second = IdempotentPaperExecutor(gateway, db.paper_orders).submit(request(), approved())

    assert second == first
    assert len(gateway.requests) == 1


def test_paper_executor_submits_approved_order_and_records_audit():
    gateway = FakePaperGateway()
    executor = IdempotentPaperExecutor(gateway)

    result = executor.submit(request(), approved())

    assert result.broker_order_id == "paper-1"
    assert executor.audit_log == (result,)
    assert gateway.requests == [request()]


def test_paper_executor_is_idempotent_for_same_client_order():
    gateway = FakePaperGateway()
    executor = IdempotentPaperExecutor(gateway)

    first = executor.submit(request(), approved())
    second = executor.submit(request(), approved())

    assert second == first
    assert len(gateway.requests) == 1
    assert len(executor.audit_log) == 1


def test_paper_executor_rejects_unapproved_order():
    gateway = FakePaperGateway()
    executor = IdempotentPaperExecutor(gateway)
    decision = RiskDecision(approved=False, quantity=Decimal("10"), reasons=("cash",))

    with pytest.raises(ValueError, match="risk gate"):
        executor.submit(request(), decision)

    assert gateway.requests == []


def test_paper_executor_rejects_quantity_exceeding_risk_approval():
    gateway = FakePaperGateway()
    executor = IdempotentPaperExecutor(gateway)

    with pytest.raises(ValueError, match="quantity"):
        executor.submit(request().different(quantity=Decimal("11")), approved())

    assert gateway.requests == []


def test_paper_executor_rejects_reused_client_id_for_different_order():
    gateway = FakePaperGateway()
    executor = IdempotentPaperExecutor(gateway)
    executor.submit(request(), approved())

    with pytest.raises(ValueError, match="different order"):
        executor.submit(
            request().different(quantity=Decimal("11")),
            RiskDecision(approved=True, quantity=Decimal("11"), reasons=()),
        )
