"""Normalize Alpaca news without inferring sentiment from headlines."""

from dataclasses import dataclass
from datetime import datetime

from alpaca.data.requests import NewsRequest


@dataclass(frozen=True)
class NewsItem:
    headline: str
    source: str
    url: str
    published_at: datetime


class AlpacaNewsProvider:
    def __init__(self, client):
        self._client = client

    def get_news(self, symbol: str, start: datetime, end: datetime) -> tuple[NewsItem, ...]:
        if (
            not symbol.strip()
            or start.utcoffset() is None
            or end.utcoffset() is None
            or start >= end
        ):
            raise ValueError("news query requires a symbol and ordered timezone-aware bounds")
        response = self._client.get_news(
            NewsRequest(symbols=symbol, start=start, end=end, limit=50)
        )
        return tuple(
            NewsItem(item.headline, item.source, item.url, item.created_at)
            for item in response.data.get("news", [])
            if item.url
            and item.headline
            and item.source
            and item.created_at.utcoffset() is not None
            and symbol.upper() in (name.upper() for name in item.symbols)
            and start <= item.created_at < end
        )
