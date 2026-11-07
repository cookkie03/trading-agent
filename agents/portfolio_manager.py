"""Portfolio Manager proposal seam; no risk approval or trade execution."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class PortfolioRequest:
    symbol: str
    analyses: Mapping[str, str]
    portfolio_context: str


@dataclass(frozen=True)
class PortfolioResult:
    decision: Literal["propose", "abstain"]
    direction: Literal["buy", "sell", "hold"] | None
    conviction: Literal["low", "medium", "high"] | None
    rationale: str
    missing_data: tuple[str, ...]


class PortfolioManager:
    """Synthesize specialist evidence through an injected backend, or abstain."""

    def __init__(self, backend: Callable[[PortfolioRequest], PortfolioResult]) -> None:
        self._backend = backend

    def evaluate(self, request: PortfolioRequest) -> PortfolioResult:
        missing = tuple(
            name
            for name in ("market", "sentiment", "technical", "fundamental", "risk")
            if not isinstance(request.analyses.get(name), str) or not request.analyses[name].strip()
        )
        if not isinstance(request.symbol, str) or not request.symbol.strip():
            missing += ("symbol",)
        if not isinstance(request.portfolio_context, str) or not request.portfolio_context.strip():
            missing += ("portfolio_context",)
        if missing:
            return PortfolioResult("abstain", None, None, "Insufficient input data", missing)
        try:
            result = self._backend(request)
        except Exception:
            return PortfolioResult("abstain", None, None, "Backend unavailable", ())
        if not isinstance(result, PortfolioResult):
            return PortfolioResult("abstain", None, None, "Invalid backend result", ())
        if result.missing_data:
            return PortfolioResult("abstain", None, None, "Insufficient data", result.missing_data)
        if (
            result.decision not in ("propose", "abstain")
            or not isinstance(result.rationale, str)
            or not result.rationale.strip()
            or (
                result.decision == "propose"
                and (
                    result.direction not in ("buy", "sell", "hold")
                    or result.conviction not in ("low", "medium", "high")
                )
            )
        ):
            return PortfolioResult("abstain", None, None, "Invalid backend result", ())
        if result.decision == "abstain":
            return PortfolioResult("abstain", None, None, result.rationale, ())
        return result
