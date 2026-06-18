"""Data fetchers — vendor-specific implementations.

Two vendor backends:
- yfinance: default, free, no API key needed
- Alpha Vantage: optional, requires API key

Each vendor module exposes the same logical functions (get_news, get_fundamentals, ...)
with vendor-prefixed names. The ``interface`` module routes calls based on config.
"""

from .utils import safe_ticker_component, save_output, get_current_date

__all__ = [
    "safe_ticker_component",
    "save_output",
    "get_current_date",
]
