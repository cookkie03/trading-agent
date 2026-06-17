from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import CharterRule, DecisionLog

DEFAULT_CHARTER: dict[str, Any] = {
    "min_risk_reward": 1.5,
    "max_position_pct": 0.10,
    "cash_reserve_pct": 0.10,
    "max_portfolio_var": 0.10,
    "base_risk_pct": 0.01,
    "heat_max_pct": 0.06,
    "max_sector_pct": 0.30,
}


def load_charter(session: Session) -> dict[str, Any]:
    """Load the whole Statute as a {key: value} dict (drives the Risk guardrails)."""
    return {r.key: r.value for r in session.scalars(select(CharterRule))}


def seed_default_charter(session: Session, overrides: Optional[dict[str, Any]] = None) -> None:
    """Insert the default Statute rules for any key not already present."""
    values = {**DEFAULT_CHARTER, **(overrides or {})}
    for key, value in values.items():
        if session.get(CharterRule, key) is None:
            set_charter_rule(session, key, value)


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


def get_charter_rule(session: Session, key: str, default: Any = None) -> Any:
    rule = session.get(CharterRule, key)
    return rule.value if rule is not None else default


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
