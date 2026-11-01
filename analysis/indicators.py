from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal


def simple_moving_average(values: Sequence[Decimal], *, window: int) -> tuple[Decimal, ...]:
    """Return the arithmetic mean for each complete trailing window."""
    if window <= 0:
        raise ValueError("window must be positive")
    if len(values) < window:
        return ()
    return tuple(
        sum(values[index - window + 1 : index + 1], Decimal("0")) / window
        for index in range(window - 1, len(values))
    )
