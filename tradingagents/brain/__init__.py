"""The brain: our multi-agent system (wiki topology).

4 desks (Market, Sentiment, Technical, Fundamentals) -> PM aggregates -> single
Risk gate -> ResearchState.

Backed by Datapizza AI agents.
"""

from .datapizza_graph import analyze_symbol
from .datapizza_llm import DatapizzaLLM
from .schemas import DeskOpinion, PMDecision, RiskDecision

__all__ = [
    "analyze_symbol",
    "DatapizzaLLM",
    "DeskOpinion",
    "PMDecision",
    "RiskDecision",
]
