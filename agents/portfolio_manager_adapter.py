"""Adapt graph analyses to the standalone Portfolio Manager without approving trades."""

from collections.abc import Callable
from typing import Any

from agents.desks import DeskOpinion
from agents.graph import Analysis
from agents.portfolio_manager import PortfolioManager, PortfolioRequest


def portfolio_manager_adapter(
    manager: PortfolioManager,
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    def run(context: dict[str, Any]) -> dict[str, Any]:
        analyses = {}
        for role, analysis in context.get("analyses", {}).items():
            if isinstance(analysis, Analysis) and analysis.role == role and analysis.content:
                opinions = [
                    value for value in analysis.content.values() if isinstance(value, DeskOpinion)
                ]
                if opinions and any(
                    not opinion.evidence
                    or not any(isinstance(item, str) and item.strip() for item in opinion.evidence)
                    for opinion in opinions
                ):
                    continue
                analyses[role] = repr(
                    {"observed_at": analysis.observed_at.isoformat(), "content": analysis.content}
                )
        result = manager.evaluate(
            PortfolioRequest(
                context.get("symbol", ""), analyses, context.get("portfolio_context", "")
            )
        )
        return {
            "decision": "pending",
            "pm_decision": result.decision,
            "direction": result.direction,
            "conviction": result.conviction,
            "rationale": result.rationale,
            "missing_data": result.missing_data,
        }

    return run
