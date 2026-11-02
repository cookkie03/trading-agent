from datetime import UTC, datetime

from workflows.triggers import TriggerEvent, TriggerQueue


def event(event_id, priority=5):
    return TriggerEvent(
        event_id=event_id,
        symbol="AAPL",
        trigger_type="next_check_date",
        reason="scheduled review",
        priority=priority,
        occurred_at=datetime(2026, 11, 2, 15, tzinfo=UTC),
        source="research_state",
    )


def test_trigger_queue_deduplicates_and_returns_high_priority_first():
    queue = TriggerQueue()
    queue.push(event("a", priority=5))
    queue.push(event("a", priority=1))
    queue.push(event("b", priority=2))

    assert queue.pop_all() == (event("a", priority=1), event("b", priority=2))
    assert queue.pop_all() == ()
