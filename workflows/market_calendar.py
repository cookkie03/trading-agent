"""Alpaca daily-bar timestamps from exchange sessions."""

from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from alpaca.trading.requests import GetCalendarRequest


def alpaca_hourly_timestamps(client, start: datetime, end: datetime) -> tuple[datetime, ...]:
    """Return whole-hour Alpaca labels overlapping regular market sessions."""
    if start.utcoffset() is None or end.utcoffset() is None or start >= end:
        raise ValueError("calendar bounds must be aware and ordered")
    eastern = ZoneInfo("America/New_York")
    sessions = client.get_calendar(
        GetCalendarRequest(
            start=start.astimezone(eastern).date(), end=end.astimezone(eastern).date()
        )
    )
    timestamps = set()
    for session in sessions:
        opening = (
            session.open.replace(tzinfo=eastern) if session.open.tzinfo is None else session.open
        )
        closing = (
            session.close.replace(tzinfo=eastern) if session.close.tzinfo is None else session.close
        )
        current = opening.astimezone(UTC).replace(minute=0, second=0, microsecond=0)
        closing = closing.astimezone(UTC)
        while current < closing:
            if start <= current and current + timedelta(hours=1) <= end:
                timestamps.add(current)
            current += timedelta(hours=1)
    return tuple(sorted(timestamps))


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
