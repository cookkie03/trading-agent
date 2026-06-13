"""
Metriche di performance e rischio.

Basato su SFC portfolio tracker analytics.py (pandas puro, zero dipendenze esterne
oltre pandas/numpy). Adatto per leggere serie dal DB del trading-agent.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def detect_frequency(dates: pd.DatetimeIndex) -> tuple[int, str]:
    """Deduce la frequenza dai gap temporali.
    Returns: (periods_per_year, label)
    """
    if len(dates) < 2:
        return (252, "day")
    diffs = pd.Series(dates).diff().dt.days.median()
    if diffs < 5:
        return (252, "day")
    elif diffs <= 15:
        return (52, "week")
    elif diffs <= 45:
        return (12, "month")
    return (4, "quarter")


def total_return(prices: pd.Series) -> float:
    if len(prices) < 2 or prices.iloc[0] == 0:
        return 0.0
    return float(prices.iloc[-1] / prices.iloc[0] - 1)


def annualized_return(prices: pd.Series, periods_per_year: int = 252) -> float:
    if len(prices) < 2 or prices.iloc[0] <= 0:
        return 0.0
    years = len(prices) / periods_per_year
    if years <= 0:
        return 0.0
    return float((prices.iloc[-1] / prices.iloc[0]) ** (1 / years) - 1)


def annualized_volatility(prices: pd.Series, periods_per_year: int = 252) -> float:
    if len(prices) < 3:
        return 0.0
    returns = prices.pct_change().dropna()
    if returns.empty:
        return 0.0
    return float(returns.std() * np.sqrt(periods_per_year))


def sharpe_ratio(prices: pd.Series, risk_free_rate: float = 0.02, periods_per_year: int = 252) -> float:
    ann_ret = annualized_return(prices, periods_per_year)
    ann_vol = annualized_volatility(prices, periods_per_year)
    if ann_vol == 0:
        return 0.0
    return float((ann_ret - risk_free_rate) / ann_vol)


def sortino_ratio(prices: pd.Series, risk_free_rate: float = 0.02, periods_per_year: int = 252) -> float:
    if len(prices) < 3:
        return 0.0
    ann_ret = annualized_return(prices, periods_per_year)
    mar = (1 + risk_free_rate) ** (1 / periods_per_year) - 1
    returns = prices.pct_change().dropna()
    downside = returns[returns - mar < 0] - mar
    downside_vol = np.sqrt(np.mean(downside ** 2)) * np.sqrt(periods_per_year) if len(downside) > 0 else 0
    if downside_vol == 0:
        return 0.0
    return float((ann_ret - risk_free_rate) / downside_vol)


def max_drawdown(prices: pd.Series) -> float:
    if prices.empty:
        return 0.0
    peak = prices.expanding(min_periods=1).max()
    dd = (prices - peak) / peak
    return float(dd.min())


def drawdown_series(prices: pd.Series) -> pd.Series:
    if prices.empty:
        return pd.Series(dtype=float)
    peak = prices.expanding(min_periods=1).max()
    return (prices - peak) / peak


def calmar_ratio(prices: pd.Series, periods_per_year: int = 252) -> float:
    ann_ret = annualized_return(prices, periods_per_year)
    mdd = abs(max_drawdown(prices))
    if mdd == 0:
        return 0.0
    return float(ann_ret / mdd)


def var_historical(prices: pd.Series, confidence: float = 0.95) -> float:
    if len(prices) < 10:
        return 0.0
    returns = prices.pct_change().dropna()
    return float(returns.quantile(1 - confidence))


def cvar_historical(prices: pd.Series, confidence: float = 0.95) -> float:
    if len(prices) < 10:
        return 0.0
    returns = prices.pct_change().dropna()
    var = returns.quantile(1 - confidence)
    return float(returns[returns <= var].mean())


def compute_alpha_beta(
    nav: pd.Series, benchmark: pd.Series, risk_free_rate: float = 0.04, periods_per_year: int = 252
) -> dict:
    """Alpha, Beta, R2, Tracking Error, Information Ratio vs benchmark."""
    aligned = pd.concat([nav, benchmark], axis=1, join="inner").dropna()
    if len(aligned) < 10:
        return {"alpha": 0, "beta": 0, "r_squared": 0, "tracking_error": 0, "info_ratio": 0, "correlation": 0}

    port_ret = aligned.iloc[:, 0].pct_change().dropna()
    bench_ret = aligned.iloc[:, 1].pct_change().dropna()

    min_len = min(len(port_ret), len(bench_ret))
    port_ret = port_ret.iloc[:min_len]
    bench_ret = bench_ret.iloc[:min_len]

    cov = np.cov(port_ret, bench_ret)
    beta = float(cov[0, 1] / cov[1, 1]) if cov[1, 1] != 0 else 0

    rf_period = (1 + risk_free_rate) ** (1 / periods_per_year) - 1
    alpha = (port_ret.mean() - rf_period) - beta * (bench_ret.mean() - rf_period)
    alpha_ann = float(alpha * periods_per_year)

    correlation = float(np.corrcoef(port_ret, bench_ret)[0, 1])
    r_squared = correlation ** 2

    excess = port_ret - bench_ret
    te = float(excess.std() * np.sqrt(periods_per_year))
    ir = float(excess.mean() * periods_per_year / te) if te > 0 else 0

    return {
        "alpha": round(alpha_ann, 4),
        "beta": round(beta, 4),
        "r_squared": round(r_squared, 4),
        "tracking_error": round(te, 4),
        "info_ratio": round(ir, 4),
        "correlation": round(correlation, 4),
    }


def summary_kpi(nav_df: pd.DataFrame, benchmark_df: pd.DataFrame | None = None) -> dict:
    """Riepilogo KPI principale per la dashboard."""
    if nav_df.empty or "total_value" not in nav_df.columns:
        return {}

    nav = nav_df.sort_values("ts")["total_value"]
    nav.index = pd.to_datetime(nav_df.sort_values("ts")["ts"])

    current = float(nav.iloc[-1])
    initial = float(nav.iloc[0]) if nav.iloc[0] > 0 else current
    since_inception = (current / initial - 1) if initial > 0 else 0

    result = {
        "NAV Corrente": current,
        "NAV Iniziale": initial,
        "Since Inception": since_inception,
        "Sharpe": sharpe_ratio(nav),
        "Sortino": sortino_ratio(nav),
        "Max Drawdown": max_drawdown(nav),
        "Calmar": calmar_ratio(nav),
        "Volatilità Ann.": annualized_volatility(nav),
        "VaR 95%": var_historical(nav),
        "CVaR 95%": cvar_historical(nav),
    }

    if benchmark_df is not None and not benchmark_df.empty and "total_value" in benchmark_df.columns:
        bench_nav = benchmark_df.sort_values("ts")["total_value"]
        bench_nav.index = pd.to_datetime(benchmark_df.sort_values("ts")["ts"])
        ab = compute_alpha_beta(nav, bench_nav)
        result["Alpha"] = ab["alpha"]
        result["Beta"] = ab["beta"]
        result["R²"] = ab["r_squared"]
        result["Info Ratio"] = ab["info_ratio"]

    return result
