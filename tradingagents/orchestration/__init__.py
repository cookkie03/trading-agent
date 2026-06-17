"""Orchestration: the cycle runner that ties the whole alpha together.

Flow (the funnel + trigger engine of the wiki):

    Trigger Engine  ->  priority queue  ->  analyze (Datapizza agents)  ->  cost gate  ->  execute

The ``analyze`` step is a pluggable hook: Datapizza agents implement the
``Analyzer`` signature; until then a ``hold_analyzer`` stub keeps the runner
fully testable without any LLM.

This module re-exports the Datapizza-based implementations, keeping backward
compatibility with the rest of the codebase (cycle.py, daemon, CLI).
"""

from .triggers import (
    TriggerEvent,
    collect_triggers,
    event_checkpoints,
    price_alerts,
    watchlist_candidates,
)
from .datapizza_analyze import Analyzer, hold_analyzer, make_brain_analyzer
from .cycle import CycleReport, run_cycle

__all__ = [
    "TriggerEvent",
    "collect_triggers",
    "event_checkpoints",
    "watchlist_candidates",
    "price_alerts",
    "Analyzer",
    "hold_analyzer",
    "make_brain_analyzer",
    "CycleReport",
    "run_cycle",
]
