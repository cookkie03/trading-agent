#!/usr/bin/env bash
set -euo pipefail

export TRADING_AGENT_DB="${TRADING_AGENT_DB:-data/trading-agent.db}"
export TRADING_AGENT_HOST="${TRADING_AGENT_HOST:-localhost}"
export TRADING_AGENT_PORT="${TRADING_AGENT_PORT:-8000}"

exec uv run python scripts/run_dashboard.py
