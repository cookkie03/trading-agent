from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ResearchState


def save_research_state(
    session: Session,
    symbol: str,
    payload: dict[str, Any],
    *,
    direction: Optional[str] = None,
    conviction: Optional[str] = None,
    status: str = "draft",
    version: str = "alpha",
) -> ResearchState:
    state = ResearchState(
        symbol=symbol,
        payload=payload,
        direction=direction,
        conviction=conviction,
        status=status,
        version=version,
    )
    session.add(state)
    session.flush()
    return state


def latest_research_state(session: Session, symbol: str) -> Optional[ResearchState]:
    stmt = (
        select(ResearchState)
        .where(ResearchState.symbol == symbol)
        .order_by(ResearchState.created_at.desc(), ResearchState.id.desc())
        .limit(1)
    )
    return session.scalar(stmt)
