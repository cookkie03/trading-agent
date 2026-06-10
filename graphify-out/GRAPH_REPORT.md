# Graph Report - .  (2026-06-10)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1343 nodes · 3334 edges · 67 communities (62 shown, 5 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 399 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c47deb45`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 66|Community 66]]

## God Nodes (most connected - your core abstractions)
1. `Session` - 58 edges
2. `init_db()` - 45 edges
3. `PaperBroker` - 43 edges
4. `reset_engine()` - 41 edges
5. `ResearchState` - 36 edges
6. `run_cycle()` - 35 edges
7. `OrderRequest` - 34 edges
8. `Direction` - 33 edges
9. `ingest_price_bars()` - 32 edges
10. `Extractors` - 31 edges

## Surprising Connections (you probably didn't know these)
- `ResearchState` --uses--> `AlpacaBroker`  [INFERRED]
  tests/test_broker.py → tradingagents/broker/alpaca.py
- `_FetcherUp` --uses--> `ResearchState`  [INFERRED]
  tests/test_brain.py → tradingagents/domain/state.py
- `FakeLLM` --uses--> `ResearchState`  [INFERRED]
  tests/test_brain.py → tradingagents/domain/state.py
- `DeskOpinion` --uses--> `ResearchState`  [INFERRED]
  tests/test_brain.py → tradingagents/domain/state.py
- `PMDecision` --uses--> `ResearchState`  [INFERRED]
  tests/test_brain.py → tradingagents/domain/state.py

## Import Cycles
- 1-file cycle: `tradingagents/ingestion/macro_ingest.py -> tradingagents/ingestion/macro_ingest.py`
- 1-file cycle: `tradingagents/ingestion/price_ingest.py -> tradingagents/ingestion/price_ingest.py`
- 1-file cycle: `tradingagents/storage/models.py -> tradingagents/storage/models.py`

## Communities (67 total, 5 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.07
Nodes (113): CharterRule, DecisionLog, DeclarativeBase, Mantainer: keep the rendicontazione (portfolio_state) up to date.  Canvas edge `, Fundamentals ingestion: vendor -> DB.  Feeds the Fundamentals desk (health, valu, Deterministic screening (the funnel's Quick Thinker).  No LLM: a cheap, explaina, Instrument, MacroPoint (+105 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (65): make_agent_context(), Per-agent context state — a context window tailored to each agent's task.  Each, Create the context structure tailored to ``agent``'s task., All accumulated tool results, flattened (across sections)., File a tool result into its task-specific section (preserving structure)., ToolRecord, analyze_batch(), Director level — fan-out per-ticker evaluators + portfolio decision.  Three-leve (+57 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (51): get_config(), initialize_config(), Initialize the configuration with default values., Update the configuration with custom values.      Dict-valued keys (e.g. ``data_, Get the current configuration., set_config(), get_category_for_method(), get_vendor() (+43 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (56): CycleReport, FundamentalsFetcher, MacroFetcher, NewsFetcher, make_brain_analyzer(), Build an Analyzer backed by the brain graph (our wiki topology)., SocialFetcher, Sp500Source (+48 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (34): ChatOpenAI, DeepSeekChatOpenAI, _input_to_messages(), MinimaxChatOpenAI, NormalizedChatOpenAI, MiniMax-specific overrides on top of the OpenAI-compatible client.      M2.x rea, ChatOpenAI with normalized content output and capability-aware binding.      The, Normalise a langchain LLM input to a list of message objects.      Accepts a lis (+26 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (37): BaseModel, PathLike, Tests for the global configuration (defaults + TOML overlay)., test_convenience_views(), test_defaults_when_no_file(), test_toml_overlay_is_partial(), Tests for the background daemon (start/stop/status lifecycle)., BenchmarkSettings (+29 more)

### Community 6 - "Community 6"
Cohesion: 0.08
Nodes (21): _candidates(), get_capabilities(), ModelCapabilities, Declarative per-model capability table for OpenAI-compatible providers.  This is, Normalised forms of an id: with/without ``provider/`` prefix and     OpenRouter, Resolve capabilities by exact ID, then pattern, then default.      Handles provi, What an OpenAI-compatible model accepts at the API level., Unit tests for the LLM capability table. (+13 more)

### Community 7 - "Community 7"
Cohesion: 0.10
Nodes (38): atr(), _closes(), compute_indicator(), ema(), high_low_52w(), max_drawdown(), Pure technical-indicator math over OHLCV bars.  A "bar" is a dict with at least, Single parametric entry point (the family-B tool surface). (+30 more)

### Community 8 - "Community 8"
Cohesion: 0.11
Nodes (31): AlphaVantageRateLimitError, _filter_csv_by_date_range(), format_datetime_for_api(), get_api_key(), _make_api_request(), Retrieve the API key for Alpha Vantage from environment variables., Convert various date formats to YYYYMMDDTHHMM format required by Alpha Vantage A, Exception raised when Alpha Vantage API rate limit is exceeded. (+23 more)

### Community 9 - "Community 9"
Cohesion: 0.15
Nodes (28): Direction, Wiki-aligned trading domain model.  This package is the executable form of the d, atr_levels(), check_guardrails(), conviction_multiplier(), passes_risk_reward(), position_size(), Deterministic risk engine.  Pure functions (no LLM) that encode the wiki's quant (+20 more)

### Community 10 - "Community 10"
Cohesion: 0.14
Nodes (27): Deterministic execution layer.  The wiki decision is that the Trader is **not**, Submit orders to a broker and reconcile their state.  Bridges the deterministic, build_trade(), can_trade(), inject_portfolio_state(), OrderProposal, persist_trade(), propose_and_record() (+19 more)

### Community 11 - "Community 11"
Cohesion: 0.12
Nodes (13): BaseLLMClient, Client for Anthropic Claude models., Validate model for Anthropic., AzureOpenAIClient, Client for Azure OpenAI deployments.      Requires environment variables:, Azure accepts any deployed model name., create_llm_client(), Create an LLM client for the specified provider.      Provider modules are impor (+5 more)

### Community 12 - "Community 12"
Cohesion: 0.17
Nodes (15): Alpaca paper-trading adapter (REST).  Network-bound; used in integration, not un, Broker, BrokerOrder, OrderRequest, OrderStatus, Broker interface and shared value objects., Minimal interface every broker adapter implements., Broker abstraction: execute orders behind a swappable adapter.  The wiki decisio (+7 more)

### Community 13 - "Community 13"
Cohesion: 0.15
Nodes (19): _Fetcher, Tests for benchmark tracking + performance/alpha (Fase 3)., test_alpha_vs_benchmark(), test_benchmark_return(), test_portfolio_return(), benchmark_return(), ingest_benchmarks(), PriceFetcher (+11 more)

### Community 14 - "Community 14"
Cohesion: 0.15
Nodes (16): PerTradeCommission, PaperBroker, manage_exits(), Close open positions whose stop or target was hit. Returns closed trades., Tests for the Trigger Engine + cycle runner., test_collect_triggers_dedup_and_order(), test_manage_exits_closes_on_take_profit(), test_run_cycle_cost_gate_skips() (+8 more)

### Community 15 - "Community 15"
Cohesion: 0.15
Nodes (19): _clamp01(), compute_screening_signals(), Compute raw screening signals + a composite score in [0, 1].      Signals (all d, Read the most recent stored bars, score the ticker, update its card., screen_ticker(), _bars(), db(), FakeFetcher (+11 more)

### Community 16 - "Community 16"
Cohesion: 0.15
Nodes (13): Deterministic long-only ATR backtest over stored bars.  Walks the bars one at a, Direction, Core enumerations of the trading domain.  The conviction/direction vocabulary is, 5-level directional signal, also used for conviction_level., Strong signals are the only ones allowed to use leverage (options)., Outcome of the Risk Analyst gate., RiskVerdict, The research_state / investment_state contract (Pydantic).  Mirrors ``state-sche (+5 more)

### Community 17 - "Community 17"
Cohesion: 0.15
Nodes (18): ForkStructuredLLM, Real structured LLM with tool calling, backed by the LangChain client.      Defa, alpaca_base_url(), Resolve the Alpaca REST base URL for ``mode`` ('paper' | 'live')., Commission-free equity (e.g. Alpaca). Spread is not modelled here., ZeroCommission, YFinanceFundamentalsFetcher, YFinanceNewsFetcher (+10 more)

### Community 18 - "Community 18"
Cohesion: 0.15
Nodes (20): execute_thesis(), Send a persisted (pending) trade to the broker and record the outcome., End-to-end: size + record the order, then submit it to the broker., Re-read the broker for every non-final trade; align the DB to it.      Broker is, reconcile_open_trades(), submit_trade(), _approved_state(), db() (+12 more)

### Community 19 - "Community 19"
Cohesion: 0.14
Nodes (15): AgentOpinion, Produce the nested document persisted as JSON (Opzione C sealing)., One desk agent's proposal. The PM aggregates these into the final call., The full investment thesis for one ticker., Completeness gate: every obligatory field filled before sealing.          A HOLD, ResearchState, _actionable_state(), ResearchState (+7 more)

### Community 20 - "Community 20"
Cohesion: 0.31
Nodes (8): _dedup_key(), ingest_news(), NewsFetcher, NewsIngestResult, News ingestion: vendor -> DB (DB-first dedup, write-through).  Feeds the Market, Return news items: dicts with ``headline`` + ``ts`` (datetime) at least., Any, Session

### Community 21 - "Community 21"
Cohesion: 0.23
Nodes (18): Orchestration: the cycle runner that ties the whole alpha together.  Flow (the f, collect_triggers(), due_checkpoints(), event_checkpoints(), price_alerts(), Trigger Engine: centralise every reason the system wakes up.  All sources (due c, Gather all sources, de-dup by symbol (keep highest priority), sort desc.      Pr, Tickers whose Dynamic Temporal Checkpoint (next_check_date) is due. (+10 more)

### Community 22 - "Community 22"
Cohesion: 0.23
Nodes (17): _fmt(), _headlines(), _macro_snapshot(), market_context(), pm_context(), Build the context strings injected into each agent.  Numbers come from the DB (r, risk_context(), sentiment_context() (+9 more)

### Community 23 - "Community 23"
Cohesion: 0.18
Nodes (16): Levels, Entry/stop/take-profit expressed first in ATR units, then as prices.      The LL, assess_costs(), CostAssessment, expected_reward(), expected_risk(), Runtime cost guardrail: does the trade's reward cover its costs?  Conservative p, Potential gross profit if the take-profit is reached. (+8 more)

### Community 24 - "Community 24"
Cohesion: 0.17
Nodes (15): admit_within_statute(), PortfolioProposal, PortfolioRiskResult, Portfolio-level risk gate (the Director's Statute, on the whole book).  Per-tick, Greedily admit buys (highest risk-adjusted first) keeping the book legal.      S, db(), _FakeLLM, _FetcherUp (+7 more)

### Community 25 - "Community 25"
Cohesion: 0.24
Nodes (7): IBKRBroker, order_action(), IBKR (TWS API) has no clean 'list the whole universe' call — the         univers, IBKR action — BUY / SELL., Any, BrokerOrder, OrderRequest

### Community 26 - "Community 26"
Cohesion: 0.21
Nodes (16): Analyzer, _admit_watchlist(), CycleReport, _log(), The cycle runner: one pass of the autonomous loop.      triggers -> analyze (gra, Learning-loop substrate: thesis + per-agent opinions + outcome., Dynamic entry: a news/alert on a non-watchlist universe ticker joins it., Run one orchestration cycle and return a report.      Three stages: (1) manage e (+8 more)

### Community 27 - "Community 27"
Cohesion: 0.19
Nodes (16): init_db(), Drop the cached engine/sessionmaker (used by tests for isolation)., Create all tables. On PostgreSQL, promote price_bars to a hypertable., reset_engine(), _cleanup(), db(), db(), db() (+8 more)

### Community 28 - "Community 28"
Cohesion: 0.18
Nodes (13): fundamentals_context(), FundamentalsFetcher, ingest_fundamentals(), Return a flat dict of valuation/health metrics., db(), FakeFund, Tests for fundamentals ingestion and its use in the brain context., test_fundamentals_context() (+5 more)

### Community 29 - "Community 29"
Cohesion: 0.20
Nodes (12): Data ingestion: vendor -> DB (the extraction layer of the wiki data-layer).  The, FredFetcher, ingest_macro(), MacroFetcher, MacroIngestResult, _naive(), Macro ingestion: FRED-style series -> DB (DB-first), for the Market desk.  Macro, Return observations: dicts with ``ts`` (datetime) and ``value`` (float). (+4 more)

### Community 30 - "Community 30"
Cohesion: 0.15
Nodes (10): get_api_key_env(), Canonical provider -> API-key env-var mapping.  A single source of truth for whi, Return the env var name for `provider`'s API key, or None if not applicable., Return configured AzureChatOpenAI instance., Default base URL for ``provider``, with env-var overrides where defined.      Cu, Client for OpenAI, Ollama, OpenRouter, and xAI providers.      For native OpenAI, Validate model for the provider., _resolve_provider_base_url() (+2 more)

### Community 31 - "Community 31"
Cohesion: 0.17
Nodes (8): get_known_models(), get_model_options(), Shared model catalog for CLI selections and validation., Return shared model options for a provider and selection mode., Build known model names from the shared CLI catalog., ModelOption, DummyLLMClient, ModelValidationTests

### Community 32 - "Community 32"
Cohesion: 0.20
Nodes (12): _chain(), Tests for the options-chain tool (selection logic, offline)., test_get_options_chain_injected(), test_select_contract_nearest_strike(), Agent tool layer (the wiki tool inventory as real callables).  These are the con, get_options_chain(), Options chain tool (leverage on Strong signals).  Fetches the option chain and s, Return option contracts (dicts with at least ``strike``). Empty if no source. (+4 more)

### Community 33 - "Community 33"
Cohesion: 0.23
Nodes (13): backtest(), BacktestResult, Run the backtest on the bars stored for ``symbol``., Simulate the long-only ATR strategy; return performance metrics., run_backtest(), Deterministic backtester (the continuous threshold validator).  Per the wiki, ba, Tests for the deterministic backtester., test_backtest_downtrend_loses() (+5 more)

### Community 34 - "Community 34"
Cohesion: 0.22
Nodes (6): AlpacaBroker, List active, tradable US-equity assets (the investable universe).          Offic, test_alpaca_account_real(), Any, BrokerOrder, OrderRequest

### Community 35 - "Community 35"
Cohesion: 0.20
Nodes (13): Engine, sessionmaker, get_engine(), get_session(), Engine, session and schema bootstrap for the persistence layer.  Connection stri, Resolve the database URL using the documented precedence., Return a process-wide cached engine (created on first use)., Transactional session scope: commit on success, rollback on error. (+5 more)

### Community 36 - "Community 36"
Cohesion: 0.20
Nodes (11): ingest_price_bars(), IngestResult, _naive(), PriceFetcher, OHLCV ingestion: fetch bars and write them through to the DB.  DB-first: histori, Drop tz info so SQLite (tz-naive) and tz-aware bars compare equal., Anything that can return OHLCV bars as a list of plain dicts.      Each bar must, Fetch bars for ``symbol`` and insert the ones not already stored. (+3 more)

### Community 37 - "Community 37"
Cohesion: 0.18
Nodes (8): ABC, BaseLLMClient, Abstract base class for LLM clients., Return the provider name used in warning messages., Warn when the model is outside the known list for the provider., Return the configured LLM instance., Validate that the model is supported by this client., Any

### Community 38 - "Community 38"
Cohesion: 0.19
Nodes (11): default_port(), map_status(), Interactive Brokers adapter — TWS API (the most complete IBKR interface).  Uses, Default TWS port: 7496 live, 7497 paper (override for IB Gateway)., OrderStatus, Offline tests for the IBKR adapter helpers (no TWS connection needed)., Needs a running TWS/IB Gateway; skipped otherwise., test_build_limit_and_market_orders() (+3 more)

### Community 39 - "Community 39"
Cohesion: 0.24
Nodes (12): disinvest_weakest(), rank_holdings_by_weakness(), Open positions ordered weakest-first (conviction, then screening score)., Close weakest holdings until ``needed_cash`` is freed. Returns closed trades., db(), Tests for rating-based disinvestment., _setup(), test_disinvest_frees_room_from_weakest() (+4 more)

### Community 40 - "Community 40"
Cohesion: 0.23
Nodes (6): _capture_kwargs(), Tests for Anthropic effort-parameter gating (#831).  Haiku 4.5 (and current Haik, Forward-compat: new Opus/Sonnet versions don't need a code change., Default is conservative — unknown models don't get effort to avoid 400s., Skipping effort must not break other passthrough kwargs., TestEffortGate

### Community 41 - "Community 41"
Cohesion: 0.23
Nodes (11): _Fetcher, Tests for the agent tool layer (real-time-first, write-through, heat)., test_realtime_quote_falls_back_to_db(), test_realtime_quote_live_first_writes_through(), test_volume_spike(), get_realtime_quote(), Current price, **real-time first** with write-through to the DB.      If a live, Detect an abnormal volume spike on the latest bar (rolling z-score). (+3 more)

### Community 42 - "Community 42"
Cohesion: 0.24
Nodes (9): Warm start: pre-run the extractors on a new (empty) analysis.  When the team sta, _dedup_key(), ingest_social(), Social-sentiment ingestion: forums/social -> DB (DB-first), for the Sentiment de, Return posts: dicts with ``ts`` (datetime), ``body`` and ``platform``., SocialFetcher, SocialIngestResult, Any (+1 more)

### Community 43 - "Community 43"
Cohesion: 0.22
Nodes (8): AzureChatOpenAI, NormalizedAzureChatOpenAI, AzureChatOpenAI with normalized content output., normalize_content(), Normalize LLM response content to a plain string.      Multiple providers (OpenA, Model name validators for each provider., Check if model name is valid for the given provider.      For ollama, openrouter, validate_model()

### Community 44 - "Community 44"
Cohesion: 0.24
Nodes (8): Render the structured, sectioned context to the text the agent reads., bind_structured(), invoke_structured_or_freetext(), Shared helpers for invoking an agent with structured output and a graceful fallb, Return ``llm.with_structured_output(schema)`` or ``None`` if unsupported.      L, Run the structured call and render to markdown; fall back to free-text on any fa, Any, T

### Community 45 - "Community 45"
Cohesion: 0.29
Nodes (7): CommissionModel, PercentCommission, PerShareCommission, Commission models (cost-accounting, runtime).  A swappable estimator of the brok, IBKR-style: per-share fee with a per-order minimum., Protocol, test_commission_models()

### Community 46 - "Community 46"
Cohesion: 0.29
Nodes (7): db(), FakeSocial, _items(), Tests for social ingestion and its use in the Sentiment context., test_ingest_social_and_dedup(), test_sentiment_context_includes_social(), test_sentiment_context_social_placeholder()

### Community 48 - "Community 48"
Cohesion: 0.22
Nodes (7): ChatAnthropic, NormalizedChatAnthropic, Whether Anthropic accepts the ``effort`` parameter for this model., ChatAnthropic with normalized content output.      Claude models with extended t, Return configured ChatAnthropic instance., _supports_effort(), Any

### Community 49 - "Community 49"
Cohesion: 0.33
Nodes (6): db(), FakeMacro, _points(), Tests for macro ingestion (DB-first) and its use in the Market context., test_ingest_macro_and_dedup(), test_market_context_includes_macro()

### Community 50 - "Community 50"
Cohesion: 0.29
Nodes (5): ChatGoogleGenerativeAI, NormalizedChatGoogleGenerativeAI, ChatGoogleGenerativeAI with normalized content output.      Gemini 3 models retu, Return configured ChatGoogleGenerativeAI instance., Any

### Community 51 - "Community 51"
Cohesion: 0.33
Nodes (7): _latest_close(), Recompute and persist the current portfolio snapshot.      With a broker, cash +, run_mantainer(), test_mantainer_marks_positions_to_market(), Broker, PortfolioSnapshot, Session

### Community 52 - "Community 52"
Cohesion: 0.48
Nodes (6): main(), _make_pm_state(), _make_rm_state(), _make_trader_state(), _print_section(), End-to-end smoke for structured-output agents against a real LLM provider.  Runs

### Community 53 - "Community 53"
Cohesion: 0.38
Nodes (4): FakeFetcher, End-to-end deterministic backbone (no LLM):      ingest bars -> ATR from DB -> A, test_data_to_trade_backbone(), _uptrend_bars()

### Community 54 - "Community 54"
Cohesion: 0.29
Nodes (6): test_open_positions_risk_heat(), get_open_positions_risk(), Portfolio tools: current open risk (portfolio heat)., Aggregate open risk (portfolio heat) across filled long positions.      heat = s, Any, Session

### Community 57 - "Community 57"
Cohesion: 0.50
Nodes (4): fetch_reddit_posts(), _fetch_subreddit(), Reddit search fetcher for ticker-specific discussion posts.  Uses Reddit's publi, Fetch recent Reddit posts mentioning ``ticker`` across finance     subreddits an

### Community 58 - "Community 58"
Cohesion: 0.50
Nodes (5): ollama, ollama_data, tradingagents, tradingagents-ollama, tradingagents_data

### Community 59 - "Community 59"
Cohesion: 0.50
Nodes (4): hold_analyzer(), Stub analyzer: a complete, approved HOLD thesis (nothing to execute)., ResearchState, Session

### Community 61 - "Community 61"
Cohesion: 0.50
Nodes (3): fetch_stocktwits_messages(), StockTwits public symbol-stream fetcher.  StockTwits exposes a per-symbol messag, Fetch recent StockTwits messages for ``ticker`` and return them as a     formatt

### Community 66 - "Community 66"
Cohesion: 0.29
Nodes (7): db(), FakeNews, _items(), Tests for news ingestion (DB-first dedup) and its use in the brain context., test_context_includes_news(), test_context_no_news_placeholder(), test_ingest_news_and_dedup()

## Knowledge Gaps
- **42 isolated node(s):** `Analyzer`, `Broker`, `CommissionModel`, `MacroFetcher`, `Session` (+37 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_settings()` connect `Community 5` to `Community 17`?**
  _High betweenness centrality (0.136) - this node is a cross-community bridge._
- **Why does `create_llm_client()` connect `Community 11` to `Community 1`, `Community 52`, `Community 17`, `Community 30`?**
  _High betweenness centrality (0.118) - this node is a cross-community bridge._
- **Why does `ResearchState` connect `Community 19` to `Community 1`, `Community 5`, `Community 9`, `Community 10`, `Community 14`, `Community 16`, `Community 18`, `Community 53`, `Community 59`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `Session` (e.g. with `CharterRule` and `DecisionLog`) actually correct?**
  _`Session` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `PaperBroker` (e.g. with `BrokerOrder` and `OrderRequest`) actually correct?**
  _`PaperBroker` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `ResearchState` (e.g. with `Direction` and `RiskVerdict`) actually correct?**
  _`ResearchState` has 8 INFERRED edges - model-reasoned connections that need verification._
- **What connects `End-to-end smoke for structured-output agents against a real LLM provider.  Runs`, `Shared pytest fixtures that prevent CI hangs when API keys are absent.`, `Tests for Anthropic effort-parameter gating (#831).  Haiku 4.5 (and current Haik` to the rest of the system?**
  _395 weakly-connected nodes found - possible documentation gaps or missing edges._