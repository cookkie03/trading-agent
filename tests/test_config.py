import pytest
from pydantic import ValidationError

from config.settings import Settings


def test_settings_use_safe_local_defaults(monkeypatch):
    for name in (
        "TRADING_AGENT_DB",
        "TRADING_AGENT_HOST",
        "TRADING_AGENT_PORT",
        "ALPACA_API_KEY",
        "ALPACA_SECRET_KEY",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = Settings(_env_file=None)

    assert settings.database_path == "data/trading-agent.db"
    assert settings.dashboard_host == "localhost"
    assert settings.dashboard_port == 8000
    assert settings.alpaca_api_key is None
    assert settings.alpaca_secret_key is None


def test_settings_parse_runtime_environment(monkeypatch):
    monkeypatch.setenv("TRADING_AGENT_DB", "/tmp/trading-agent.db")
    monkeypatch.setenv("TRADING_AGENT_HOST", "[IP_REDACTED]")
    monkeypatch.setenv("TRADING_AGENT_PORT", "8123")
    monkeypatch.setenv("ALPACA_API_KEY", "key")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "secret")

    settings = Settings(_env_file=None)

    assert settings.database_path == "/tmp/trading-agent.db"
    assert settings.dashboard_host == "[IP_REDACTED]"
    assert settings.dashboard_port == 8123
    assert settings.alpaca_api_key.get_secret_value() == "key"
    assert settings.alpaca_secret_key.get_secret_value() == "secret"


def test_settings_reject_partial_alpaca_credentials(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "key")
    monkeypatch.delenv("ALPACA_SECRET_KEY", raising=False)

    with pytest.raises(ValidationError, match="ALPACA_SECRET_KEY"):
        Settings(_env_file=None)
