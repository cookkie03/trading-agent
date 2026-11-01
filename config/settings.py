"""Validated settings loaded from environment variables."""

from __future__ import annotations

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings shared by command-line jobs and the dashboard."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_path: str = Field("data/trading-agent.db", alias="TRADING_AGENT_DB")
    dashboard_host: str = Field("localhost", alias="TRADING_AGENT_HOST")
    dashboard_port: int = Field(8000, alias="TRADING_AGENT_PORT")
    alpaca_api_key: SecretStr | None = Field(None, alias="ALPACA_API_KEY")
    alpaca_secret_key: SecretStr | None = Field(None, alias="ALPACA_SECRET_KEY")
    alpaca_trading_url: str = Field(
        "https://paper-api.alpaca.markets/v2",
        alias="ALPACA_TRADING_URL",
    )

    @model_validator(mode="after")
    def require_complete_alpaca_credentials(self) -> Settings:
        if (self.alpaca_api_key is None) != (self.alpaca_secret_key is None):
            missing = "ALPACA_SECRET_KEY" if self.alpaca_api_key is not None else "ALPACA_API_KEY"
            raise ValueError(f"{missing} must be set when Alpaca credentials are configured")
        return self
