
from datetime import date, datetime, timezone
from typing import Any, Optional

from sqlalchemy import (
    Date,
    DateTime,
    Integer,
    String,
    Index,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Area: tesi — sealed research_state / investment_state (Opzione C → JSON)
# ---------------------------------------------------------------------------
class ResearchState(Base):
    """Sealed investment thesis persisted as a JSON document.

    At runtime the state works flat; at sealing it is structured and written
    here (``payload``). The key decision fields are also promoted to columns so
    they can be filtered without parsing the JSON.
    """

    __tablename__ = "research_states"
    __table_args__ = (
        Index("ix_research_states_symbol_created", "symbol", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    as_of: Mapped[Optional[date]] = mapped_column(Date, default=None)
    version: Mapped[str] = mapped_column(String(16), default="alpha")
    status: Mapped[str] = mapped_column(String(16), default="draft")  # draft/complete/approved/declined
    direction: Mapped[Optional[str]] = mapped_column(String(16), default=None)
    conviction: Mapped[Optional[str]] = mapped_column(String(16), default=None)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
