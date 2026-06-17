"""The brain: our wiki topology as Datapizza Agents.

Replaces the LangGraph StateGraph with a pipeline of Datapizza Agents:
  4 desks (market, sentiment, technical, fundamentals) -> PM -> Risk

Each desk agent is a Datapizza Agent with its own tools and structured output.
The PM aggregates desk opinions into a final call.
The Risk agent is the single bear gate.

The LLM interface is duck-typed: uses llm._client if available (real DatapizzaLLM),
otherwise falls back to llm.generate() directly (test/fake LLMs like _FakeLLM).
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Optional

from sqlalchemy.orm import Session

from ..domain.enums import Direction, RiskVerdict
from ..domain.risk import atr_levels, check_guardrails, conviction_multiplier, position_size
from ..domain.state import AgentOpinion, ResearchState
from ..execution import inject_portfolio_state
from ..indicators import atr_from_db, indicator_snapshot
from ..tools import get_open_positions_risk, get_realtime_quote
from . import context, prompts
from .agent_context import AgentContext, make_agent_context
from .datapizza_tools import Extractors, build_desk_tools
from .schemas import DeskOpinion, PMDecision, RiskDecision


def _set_opinion(rs: ResearchState, agent: str, op: DeskOpinion) -> None:
    rs.agent_opinions = [o for o in rs.agent_opinions if o.agent != agent]
    rs.agent_opinions.append(
        AgentOpinion(
            agent=agent,
            suggested_direction=op.suggested_direction,
            suggested_conviction=op.suggested_conviction,
            rationale=op.rationale,
        )
    )


def _get_llm_client(llm):
    """Extract the Datapizza client from the LLM, or None for fake/test LLMs."""
    return getattr(llm, "_client", None)


def _run_desk_agent(
    agent_name: str,
    prompt: str,
    session: Session,
    symbol: str,
    llm: Any,
    research_state: ResearchState,
    ctx_fn,
    extractors: Optional[Extractors],
    agent_contexts: dict[str, AgentContext],
) -> None:
    """Run a single desk agent and update the research state.

    Uses Datapizza Agent if llm has a _client (real mode), otherwise falls back
    to llm.generate() directly (test/fake mode).
    """
    ctx = agent_contexts.get(agent_name) or make_agent_context(
        agent_name, injected=ctx_fn(session, symbol)
    )
    ctx.rounds += 1
    client = _get_llm_client(llm)

    if client is not None:
        # Real mode: Datapizza Agent with tool calling
        from datapizza.agents import Agent
        tools = build_desk_tools(session, agent_name, extractors)
        desk_agent = Agent(
            name=agent_name, client=client, system_prompt=prompt,
            tools=tools, output_cls=DeskOpinion, max_steps=5,
        )
        op = desk_agent.run(ctx.render())
    else:
        # Test/fake mode: direct generate call (no _client needed)
        op = llm.generate(prompt, ctx.render(), DeskOpinion)

    agent_contexts[agent_name] = ctx
    setattr(research_state, f"{agent_name}_view", op.view)
    _set_opinion(research_state, agent_name, op)


def _run_pm(
    session: Session,
    symbol: str,
    llm: Any,
    research_state: ResearchState,
    base_risk_pct: float = 0.01,
) -> None:
    """Run the Portfolio Manager agent — aggregates desk opinions into final call."""
    opinions = [o.model_dump(mode="json") for o in research_state.agent_opinions]
    client = _get_llm_client(llm)

    if client is not None:
        from datapizza.agents import Agent
        pm_agent = Agent(
            name="pm", client=client, system_prompt=prompts.PM,
            output_cls=PMDecision, max_steps=3,
        )
        result = pm_agent.run(context.pm_context(session, symbol, opinions))
    else:
        result = llm.generate(prompts.PM, context.pm_context(session, symbol, opinions), PMDecision)

    research_state.direction = result.direction
    research_state.conviction_level = result.conviction
    research_state.pro = result.pro
    research_state.contro = result.contro
    research_state.next_check_date = date.today() + timedelta(days=max(1, result.next_check_days))

    snap_atr = atr_from_db(session, symbol)
    last_close = get_realtime_quote(session, symbol)
    research_state.current_price = last_close

    if result.direction.is_actionable and snap_atr and last_close:
        research_state.levels = atr_levels(
            last_close, snap_atr, result.direction,
            k_entry=result.k_entry, k_stop=result.k_stop, k_tp=result.k_tp,
        )
        research_state.position_sizing_pct = base_risk_pct * conviction_multiplier(result.direction)


def _run_risk(
    session: Session,
    symbol: str,
    llm: Any,
    research_state: ResearchState,
    charter: Optional[dict[str, Any]],
    base_risk_pct: float,
    agent_contexts: dict[str, AgentContext],
) -> None:
    """Run the Risk Analyst agent — the single bear gate."""
    if research_state.direction is None or not research_state.direction.is_actionable or research_state.levels is None:
        research_state.risk.verdict = RiskVerdict.APPROVED
        research_state.risk.rationale = "No actionable position; nothing to gate."
        return

    from ..storage import repository as _repo

    portfolio = inject_portfolio_state(session)
    portfolio_value = portfolio.get("total_value", 0.0)
    heat = get_open_positions_risk(session)["heat_pct"]
    heat_max = (charter or {}).get("heat_max_pct", 0.06)
    portfolio["heat_pct"] = heat
    portfolio["sector"] = _repo.instrument_sector(session, symbol)
    portfolio["sector_exposure"] = _repo.sector_exposure(session)
    stop_distance = abs(research_state.levels.entry_price - research_state.levels.stop_loss)
    sizing = position_size(
        portfolio_value, research_state.levels.entry_price, stop_distance, research_state.direction,
        base_risk_pct=base_risk_pct, heat_used_pct=heat, heat_max_pct=heat_max,
    )
    guardrails = check_guardrails(
        levels=research_state.levels, sizing=sizing, charter=charter, portfolio=portfolio,
        side="buy" if research_state.direction.is_long else "sell",
    )
    research_state.risk.guardrail_checks = guardrails

    sealed = research_state.seal()
    rctx = agent_contexts.get("risk") or make_agent_context(
        "risk", injected=context.risk_context(session, symbol, sealed, guardrails)
    )
    rctx.rounds += 1
    client = _get_llm_client(llm)

    if client is not None:
        from datapizza.agents import Agent
        tools = build_desk_tools(session, "risk", None)
        risk_agent = Agent(
            name="risk", client=client, system_prompt=prompts.RISK,
            tools=tools, output_cls=RiskDecision, max_steps=5,
        )
        result = risk_agent.run(rctx.render())
    else:
        result = llm.generate(prompts.RISK, rctx.render(), RiskDecision)

    agent_contexts["risk"] = rctx
    research_state.risk.rationale = result.rationale

    # Hard guardrail failure is binding regardless of the LLM's call
    if not guardrails.get("all_ok", True):
        research_state.risk.verdict = RiskVerdict.SEND_BACK
    else:
        research_state.risk.verdict = result.verdict


def analyze_symbol(
    session: Session,
    symbol: str,
    llm: Any,
    *,
    max_revisions: int = 1,
    charter: Optional[dict[str, Any]] = None,
    base_risk_pct: float = 0.01,
    extractors: Optional[Extractors] = None,
) -> ResearchState:
    """Run the brain for one ticker and return the (possibly approved) thesis.

    Pipeline: 4 desks -> PM -> Risk (with optional revision loop).
    Replaces the LangGraph-based analyze_symbol from graph.py.
    """
    if charter is None:
        from ..storage import repository as repo
        charter = repo.load_charter(session) or None

    # Warm start: pre-run extractors so agents' first context is populated
    if extractors is not None:
        from .warmup import warm_start
        warm_start(session, symbol, extractors)

    research_state = ResearchState(ticker=symbol)
    agent_contexts: dict[str, AgentContext] = {}

    for revision in range(max_revisions + 1):
        # --- 4 desk agents (sequential, each with own tools) ---
        _run_desk_agent("market", prompts.MARKET, session, symbol, llm,
                        research_state, context.market_context, extractors, agent_contexts)
        _run_desk_agent("sentiment", prompts.SENTIMENT, session, symbol, llm,
                        research_state, context.sentiment_context, extractors, agent_contexts)
        _run_desk_agent("technical", prompts.TECHNICAL, session, symbol, llm,
                        research_state, context.technical_context, extractors, agent_contexts)
        _run_desk_agent("fundamental", prompts.FUNDAMENTALS, session, symbol, llm,
                        research_state, context.fundamentals_context, extractors, agent_contexts)

        # --- PM aggregator ---
        _run_pm(session, symbol, llm, research_state, base_risk_pct)

        # --- Risk gate ---
        _run_risk(session, symbol, llm, research_state, charter, base_risk_pct, agent_contexts)

        # --- Check if revision is needed ---
        wants_more = research_state.risk.verdict is RiskVerdict.SEND_BACK
        if not wants_more or revision >= max_revisions:
            break

    return research_state
