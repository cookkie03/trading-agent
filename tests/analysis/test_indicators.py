from decimal import Decimal

import pytest

from analysis.indicators import simple_moving_average


def test_simple_moving_average_returns_values_after_full_window() -> None:
    values = (Decimal("10"), Decimal("11"), Decimal("13"), Decimal("16"))

    assert simple_moving_average(values, window=3) == (
        Decimal("11.33333333333333333333333333"),
        Decimal("13.33333333333333333333333333"),
    )


def test_simple_moving_average_rejects_non_positive_window() -> None:
    with pytest.raises(ValueError, match="window must be positive"):
        simple_moving_average((Decimal("10"),), window=0)
