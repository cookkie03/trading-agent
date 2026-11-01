from decimal import Decimal

import pytest

from analysis.indicators import (
    average_true_range,
    exponential_moving_average,
    moving_average_convergence_divergence,
    pivot_points,
    relative_strength_index,
    simple_moving_average,
)


def test_simple_moving_average_returns_values_after_full_window() -> None:
    values = (Decimal("10"), Decimal("11"), Decimal("13"), Decimal("16"))

    assert simple_moving_average(values, window=3) == (
        Decimal("11.33333333333333333333333333"),
        Decimal("13.33333333333333333333333333"),
    )


def test_simple_moving_average_rejects_non_positive_window() -> None:
    with pytest.raises(ValueError, match="window must be positive"):
        simple_moving_average((Decimal("10"),), window=0)


def test_exponential_moving_average_uses_first_sma_as_seed() -> None:
    assert exponential_moving_average(
        tuple(Decimal(value) for value in ("10", "12", "14", "16")), window=3
    ) == (Decimal("12"), Decimal("14"))


def test_relative_strength_index_uses_wilder_smoothing() -> None:
    values = tuple(Decimal(value) for value in ("1", "2", "3", "2", "2"))
    assert relative_strength_index(values, window=3) == (
        Decimal("66.66666666666666666666666667"),
        Decimal("66.66666666666666666666666667"),
    )


def test_macd_returns_line_signal_and_histogram() -> None:
    line, signal, histogram = moving_average_convergence_divergence(
        tuple(Decimal(value) for value in ("1", "2", "3", "4", "5", "6")),
        fast_window=2,
        slow_window=3,
        signal_window=2,
    )
    assert line == (Decimal("0.5"), Decimal("0.5"), Decimal("0.5"), Decimal("0.5"))
    assert signal == (Decimal("0.5"), Decimal("0.5"), Decimal("0.5"))
    assert histogram == (Decimal("0"), Decimal("0"), Decimal("0"))


def test_average_true_range_uses_previous_close() -> None:
    highs = tuple(Decimal(value) for value in ("10", "12", "13", "14"))
    lows = tuple(Decimal(value) for value in ("8", "9", "10", "11"))
    closes = tuple(Decimal(value) for value in ("9", "11", "12", "13"))
    assert average_true_range(highs, lows, closes, window=2) == (
        Decimal("3"),
        Decimal("3"),
    )


def test_pivot_points_returns_classic_levels() -> None:
    assert pivot_points((Decimal("10"),), (Decimal("4"),), (Decimal("7"),)) == (
        (Decimal("7"), Decimal("4"), Decimal("10"), Decimal("13"), Decimal("1")),
    )
