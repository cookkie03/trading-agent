"""Shared helpers for the execution layer."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from ..storage import repository as repo


def latest_close(session: Session, symbol: str) -> Optional[float]:
    """Latest stored close price for a symbol (None if no bars)."""
    bar = repo.latest_price(session, symbol)
    return bar.close if bar is not None else None
