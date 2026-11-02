"""Centralized, deduplicated trigger queue for event-driven research runs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TriggerEvent:
    event_id: str
    symbol: str
    trigger_type: str
    reason: str
    priority: int
    occurred_at: datetime
    source: str

    def __post_init__(self) -> None:
        if not self.event_id.strip() or not self.symbol.strip():
            raise ValueError("trigger identity must not be empty")
        if self.priority < 0:
            raise ValueError("priority must not be negative")


class TriggerQueue:
    def __init__(self) -> None:
        self._events: dict[str, TriggerEvent] = {}

    def push(self, event: TriggerEvent) -> None:
        current = self._events.get(event.event_id)
        if current is None or event.priority < current.priority:
            self._events[event.event_id] = event

    def pop_all(self) -> tuple[TriggerEvent, ...]:
        events = tuple(
            sorted(self._events.values(), key=lambda item: (item.priority, item.occurred_at))
        )
        self._events.clear()
        return events
