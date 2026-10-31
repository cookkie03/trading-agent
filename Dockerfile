FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONPATH=/app \
    TRADING_AGENT_DB=/app/data/trading-agent.db \
    TRADING_AGENT_HOST= \
    TRADING_AGENT_PORT=8000

COPY --from=ghcr.io/astral-sh/uv:0.9.17 /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --extra openbb --no-dev --no-install-project

COPY agents ./agents
COPY analysis ./analysis
COPY brokers ./brokers
COPY data ./data
COPY execution ./execution
COPY interface ./interface
COPY storage ./storage
COPY tools ./tools
COPY workflows ./workflows
COPY scripts ./scripts
RUN mkdir -p /app/data

EXPOSE 8000
VOLUME ["/app/data"]

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "from urllib.request import urlopen; urlopen('http://[IP_REDACTED]:8000/api/health', timeout=2)"

CMD ["uv", "run", "--no-sync", "python", "scripts/run_dashboard.py"]
