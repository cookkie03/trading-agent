from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

_ZERO = Decimal("0")
_ONE_HUNDRED = Decimal("100")
_TWO = Decimal("2")


def _require_window(window: int) -> None:
    if window <= 0:
        raise ValueError("window must be positive")


def simple_moving_average(values: Sequence[Decimal], *, window: int) -> tuple[Decimal, ...]:
    """Return the arithmetic mean for each complete trailing window."""
    _require_window(window)
    if len(values) < window:
        return ()
    return tuple(
        sum(values[index - window + 1 : index + 1], _ZERO) / window
        for index in range(window - 1, len(values))
    )


def exponential_moving_average(values: Sequence[Decimal], *, window: int) -> tuple[Decimal, ...]:
    """Return EMA values seeded with the first complete SMA window."""
    _require_window(window)
    if len(values) < window:
        return ()
    multiplier = _TWO / (window + 1)
    average = sum(values[:window], _ZERO) / window
    result = [average]
    for value in values[window:]:
        average = (value - average) * multiplier + average
        result.append(average)
    return tuple(result)


def relative_strength_index(values: Sequence[Decimal], *, window: int) -> tuple[Decimal, ...]:
    """Return Wilder RSI values, beginning after the first complete change window."""
    _require_window(window)
    if len(values) <= window:
        return ()
    changes = [values[i] - values[i - 1] for i in range(1, len(values))]
    gains = [max(change, _ZERO) for change in changes]
    losses = [max(-change, _ZERO) for change in changes]
    average_gain = sum(gains[:window], _ZERO) / window
    average_loss = sum(losses[:window], _ZERO) / window

    def rsi() -> Decimal:
        if average_loss == _ZERO:
            return _ONE_HUNDRED if average_gain else Decimal("50")
        relative_strength = average_gain / average_loss
        return _ONE_HUNDRED - (_ONE_HUNDRED / (1 + relative_strength))

    result = [rsi()]
    for gain, loss in zip(gains[window:], losses[window:], strict=True):
        average_gain = (average_gain * (window - 1) + gain) / window
        average_loss = (average_loss * (window - 1) + loss) / window
        result.append(rsi())
    return tuple(result)


def moving_average_convergence_divergence(
    values: Sequence[Decimal],
    *,
    fast_window: int = 12,
    slow_window: int = 26,
    signal_window: int = 9,
) -> tuple[tuple[Decimal, ...], tuple[Decimal, ...], tuple[Decimal, ...]]:
    """Return MACD line, signal line, and histogram using EMA components."""
    _require_window(fast_window)
    _require_window(slow_window)
    _require_window(signal_window)
    if fast_window >= slow_window:
        raise ValueError("fast_window must be less than slow_window")
    fast = exponential_moving_average(values, window=fast_window)
    slow = exponential_moving_average(values, window=slow_window)
    macd = tuple(
        fast[index + slow_window - fast_window] - slow[index] for index in range(len(slow))
    )
    signal = exponential_moving_average(macd, window=signal_window)
    histogram = tuple(
        macd[index + signal_window - 1] - signal[index] for index in range(len(signal))
    )
    return macd, signal, histogram


def average_true_range(
    highs: Sequence[Decimal],
    lows: Sequence[Decimal],
    closes: Sequence[Decimal],
    *,
    window: int,
) -> tuple[Decimal, ...]:
    """Return Wilder ATR values from aligned high, low, and close series."""
    _require_window(window)
    if not (len(highs) == len(lows) == len(closes)):
        raise ValueError("highs, lows, and closes must have equal length")
    if len(closes) <= window:
        return ()
    true_ranges = [
        max(high - low, abs(high - previous_close), abs(low - previous_close))
        for high, low, previous_close in zip(highs[1:], lows[1:], closes[:-1], strict=True)
    ]
    average = sum(true_ranges[:window], _ZERO) / window
    result = [average]
    for true_range in true_ranges[window:]:
        average = (average * (window - 1) + true_range) / window
        result.append(average)
    return tuple(result)


def pivot_points(
    highs: Sequence[Decimal],
    lows: Sequence[Decimal],
    closes: Sequence[Decimal],
) -> tuple[tuple[Decimal, Decimal, Decimal, Decimal, Decimal], ...]:
    """Return classic next-period pivot, support, and resistance levels."""
    if not (len(highs) == len(lows) == len(closes)):
        raise ValueError("highs, lows, and closes must have equal length")
    return tuple(
        (
            pivot := (high + low + close) / 3,
            2 * pivot - high,
            2 * pivot - low,
            pivot + (high - low),
            pivot - (high - low),
        )
        for high, low, close in zip(highs, lows, closes, strict=True)
    )
