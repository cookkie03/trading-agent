"""The brain: our multi-agent system (wiki topology).

2 desks (Market+Sentiment, Technical+Fundamentals) -> PM aggregates -> single
Risk gate -> ResearchState.

Now backed by Datapizza AI agents (no LangGraph/LangChain dependency).
The old graph.py and llm.py are kept for backward compatibility during migration.
"""

from .datapizza_graph import analyze_symbol
from .datapizza_llm import DatapizzaLLM
from .schemas import DeskOpinion, PMDecision, RiskDecision

# Backward compatibility aliases
StructuredLLM = DatapizzaLLM
ForkStructuredLLM = DatapizzaLLM

__all__ = [
    "analyze_symbol",
    "DatapizzaLLM",
    "StructuredLLM",
    "ForkStructuredLLM",
    "DeskOpinion",
    "PMDecision",
    "RiskDecision",
]
