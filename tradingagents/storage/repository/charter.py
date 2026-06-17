from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import CharterRule, DecisionLog


def log_decision(
    session: Session,
    *,
    symbol: str,
    direction: Optional[str] = None,
    conviction: Optional[str] = None,
    risk_verdict: Optional[str] = None,
    agent_opinions: Optional[list[dict[str, Any]]] = None,
    payload: Optional[dict[str, Any]] = None,
    traded: bool = False,
    client_order_id: Optional[str] = None,
) -> DecisionLog:
    """Record a deep-dive decision for the learning loop (thesis <-> outcome)."""
    entry = DecisionLog(
        symbol=symbol,
        direction=direction,
        conviction=conviction,
        risk_verdict=risk_verdict,
        agent_opinions=agent_opinions or [],
        payload=payload or {},
        traded=traded,
        client_order_id=client_order_id,
    )
    session.add(entry)
    session.flush()
    return entry


def recent_decisions(
    session: Session, symbol: Optional[str] = None, *, limit: int = 20
) -> list[DecisionLog]:
    stmt = select(DecisionLog).order_by(DecisionLog.ts.desc(), DecisionLog.id.desc()).limit(limit)
    if symbol is not None:
        stmt = (
            select(DecisionLog)
            .where(DecisionLog.symbol == symbol)
            .order_by(DecisionLog.ts.desc(), DecisionLog.id.desc())
            .limit(limit)
        )
    return list(session.scalars(stmt))


def set_charter_rule(
    session: Session, key: str, value: Any, description: Optional[str] = None
) -> CharterRule:
    rule = session.get(CharterRule, key)
    if rule is None:
        rule = CharterRule(key=key, value=value, description=description)
        session.add(rule)
    else:
        rule.value = value
        if description is not None:
            rule.description = description
        rule.updated_at = datetime.now(timezone.utc)
    session.flush()
    return rule
