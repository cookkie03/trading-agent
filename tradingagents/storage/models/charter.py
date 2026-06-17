
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import (
    DateTime,
    String,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Area: costituzione / charter (Statuto)
# ---------------------------------------------------------------------------
class CharterRule(Base):
    """A deterministic Statute parameter (the textual charter -> parameter card).

    Stored as key -> JSON value so the Risk Analyst's deterministic guardrails
    read their thresholds from the DB rather than from hardcoded constants.
    """

    __tablename__ = "charter"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[Any] = mapped_column(JSON)
    description: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )
