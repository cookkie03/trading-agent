"""Research graph with injected agents and deterministic safety checks.

This graph does not execute trades. Its routing is provisional: the risk
analyst contributes alongside the specialists, while an independent gate
checks a PM proposal before any approval. The caller must supply a trusted
clock for live use; a state timestamp is intended only for controlled replay.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

ROLES = ("market", "sentiment", "technical", "fundamental", "risk")


@dataclass(frozen=True)
class Analysis:
    role: str
    observed_at: datetime
    content: Mapping[str, Any]


class AgentState(TypedDict, total=False):
    context: dict[str, Any]
    now: datetime
    analyses: dict[str, Analysis]
    proposal: dict[str, Any]
    decision: str
    reason: str


def build_agent_graph(
    *,
    analysts: Mapping[str, Callable[[dict[str, Any]], Analysis]],
    portfolio_manager: Callable[[dict[str, Any]], dict[str, Any]],
    risk_gate: Callable[[dict[str, Any]], bool],
    max_age: timedelta,
    clock: Callable[[], datetime] | None = None,
    proposal_complete: Callable[[dict[str, Any]], bool],
    checkpointer: Any = None,
) -> Any:
    if set(analysts) != set(ROLES):
        raise ValueError("exactly five specialist analysts are required")
    if max_age <= timedelta(0):
        raise ValueError("max_age must be positive")

    graph = StateGraph(AgentState)

    def analyze(state: AgentState) -> dict[str, Any]:
        try:
            now = clock() if clock else state["now"]
            if now.tzinfo is None or now.utcoffset() is None:
                raise ValueError("now must have a timezone")
            results = {}
            for role in ROLES:
                result = deepcopy(analysts[role](deepcopy(state["context"])))
                if not isinstance(result, Analysis) or result.role != role or not result.content:
                    raise ValueError(f"invalid analysis: {role}")
                if result.observed_at.tzinfo is None or result.observed_at.utcoffset() is None:
                    raise ValueError(f"timestamp requires timezone: {role}")
                age = now - result.observed_at
                if age < timedelta(0) or age > max_age:
                    raise ValueError(f"analysis not current: {role}")
                results[role] = result
            return {"analyses": results, "reason": ""}
        except Exception as exc:
            return {"analyses": {}, "reason": f"analysis unavailable: {exc}"}

    def decide(state: AgentState) -> dict[str, Any]:
        if state.get("reason"):
            return {"decision": "pending", "proposal": {}}
        try:
            context = deepcopy({**state["context"], "analyses": state["analyses"]})
            proposal = portfolio_manager(deepcopy(context))
            if not isinstance(proposal, dict) or proposal.get("decision") not in (
                "approve",
                "reject",
                "pending",
            ):
                return {"proposal": {}, "decision": "pending", "reason": "invalid PM proposal"}
            if proposal["decision"] != "approve":
                return {
                    "proposal": proposal,
                    "decision": "rejected" if proposal["decision"] == "reject" else "pending",
                }
            if proposal_complete(deepcopy(proposal)) is not True:
                return {
                    "proposal": proposal,
                    "decision": "pending",
                    "reason": "incomplete proposal",
                }
            now = clock() if clock else state["now"]
            if (
                now.tzinfo is None
                or now.utcoffset() is None
                or any(
                    not timedelta(0) <= now - item.observed_at <= max_age
                    for item in state["analyses"].values()
                )
            ):
                return {
                    "proposal": proposal,
                    "decision": "pending",
                    "reason": "analysis not current",
                }
            approved = risk_gate(deepcopy({**context, "proposal": proposal}))
            if approved is not True:
                return {
                    "proposal": proposal,
                    "decision": "rejected",
                    "reason": "risk gate did not approve",
                }
            return {"proposal": proposal, "decision": "approved", "reason": ""}
        except Exception as exc:
            return {"proposal": {}, "decision": "pending", "reason": f"decision unavailable: {exc}"}

    graph.add_node("analysts", analyze)
    graph.add_node("portfolio_manager", decide)
    graph.add_edge(START, "analysts")
    graph.add_edge("analysts", "portfolio_manager")
    graph.add_edge("portfolio_manager", END)
    return graph.compile(checkpointer=checkpointer)
