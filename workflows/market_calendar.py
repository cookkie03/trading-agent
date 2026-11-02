"""Alpaca daily-bar timestamps from exchange sessions."""

from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

from alpaca.trading.requests import GetCalendarRequest


def alpaca_daily_timestamps(client, start: datetime, end: datetime) -> tuple[datetime, ...]:
    """Return daily bar labels for regular sessions in [start, end)."""
    if start.utcoffset() is None or end.utcoffset() is None or start >= end:
        raise ValueError("calendar bounds must be aware and ordered")
    eastern = ZoneInfo("America/New_York")
    request = GetCalendarRequest(
        start=start.astimezone(eastern).date(), end=end.astimezone(eastern).date()
    )
    sessions = client.get_calendar(request)
    timestamps = (
        datetime.combine(session.date, time.min, eastern).astimezone(UTC) for session in sessions
    )
    return tuple(sorted(timestamp for timestamp in timestamps if start <= timestamp < end))
