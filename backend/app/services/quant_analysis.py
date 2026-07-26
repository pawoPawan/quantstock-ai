"""
Quantitative analysis service.

Computes risk-adjusted performance metrics, portfolio analytics,
Monte Carlo simulation using GBM, VaR/CVaR, and Kelly Criterion.
"""

import logging
import math
import random
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)

TRADING_DAYS = 252
RISK_FREE_RATE = 0.0525


# ─── Return Series ────────────────────────────────────────────────────────────

def compute_returns(prices: List[float], method: str = "log") -> np.ndarray:
    """Compute daily log or simple returns."""
    arr = np.array(prices, dtype=float)
    if method == "log":
        return np.diff(np.log(arr))
    return np.diff(arr) / arr[:-1]


def annualized_return(returns: np.ndarray) -> float:
    """Geometric annualized return from daily returns."""
    if len(returns) == 0:
        return 0.0
    total = np.expm1(np.sum(returns)) if True else np.prod(1 + returns) - 1
    return float((1 + total) ** (TRADING_DAYS / len(returns)) - 1)


def annualized_volatility(returns: np.ndarray) -> float:
    return float(np.std(returns, ddof=1) * math.sqrt(TRADING_DAYS))


# ─── Risk-Adjusted Ratios ────────────────────────────────────────────────────

def sharpe_ratio(returns: np.ndarray, rf: float = RISK_FREE_RATE) -> float:
    """
    Sharpe Ratio = (Rp - Rf) / σp

    Source: Sharpe (1966) — Mutual Fund Performance, JBusiness.
    """
    mu = annualized_return(returns)
    sigma = annualized_volatility(returns)
    if sigma == 0:
        return 0.0
    return round((mu - rf) / sigma, 4)


def sortino_ratio(returns: np.ndarray, rf: float = RISK_FREE_RATE, target: float = 0.0) -> float:
    """
    Sortino Ratio = (Rp - Rf) / σ_downside

    Only penalizes downside volatility below target return.
    Source: Sortino & van der Meer (1991) — Journal of Portfolio Management.
    """
    daily_target = target / TRADING_DAYS
    downside = returns[returns < daily_target] - daily_target
    downside_std = math.sqrt(np.mean(downside ** 2)) * math.sqrt(TRADING_DAYS) if len(downside) > 0 else 0
    mu = annualized_return(returns)
    if downside_std == 0:
        return 0.0
    return round((mu - rf) / downside_std, 4)


def treynor_ratio(returns: np.ndarray, beta: float, rf: float = RISK_FREE_RATE) -> float:
    """Treynor Ratio = (Rp - Rf) / Beta"""
    if beta == 0:
        return 0.0
    mu = annualized_return(returns)
    return round((mu - rf) / beta, 4)


def calmar_ratio(returns: np.ndarray) -> float:
    """Calmar Ratio = Annualized Return / |Max Drawdown|"""
    ann_ret = annualized_return(returns)
    mdd = max_drawdown(returns)["max_drawdown"]
    if abs(mdd) < 1e-8:
        return 0.0
    return round(ann_ret / abs(mdd), 4)


def omega_ratio(returns: np.ndarray, threshold: float = 0.0) -> float:
    """
    Omega Ratio = Σ gains above threshold / Σ losses below threshold.
    Source: Keating & Shadwick (2002).
    """
    daily_thresh = threshold / TRADING_DAYS
    gains = np.sum(returns[returns > daily_thresh] - daily_thresh)
    losses = np.sum(daily_thresh - returns[returns <= daily_thresh])
    if losses == 0:
        return float("inf")
    return round(gains / losses, 4)


def information_ratio(returns: np.ndarray, benchmark_returns: np.ndarray) -> float:
    """Information Ratio = (Rp - Rb) / TrackingError"""
    if len(returns) != len(benchmark_returns):
        min_len = min(len(returns), len(benchmark_returns))
        returns = returns[-min_len:]
        benchmark_returns = benchmark_returns[-min_len:]
    active = returns - benchmark_returns
    te = annualized_volatility(active)
    if te == 0:
        return 0.0
    return round(annualized_return(active) / te, 4)


# ─── Drawdown ─────────────────────────────────────────────────────────────────

def max_drawdown(returns: np.ndarray) -> Dict[str, Any]:
    """
    Maximum Drawdown: largest peak-to-trough decline.
    Returns both the magnitude and the duration (in trading days).
    """
    cum_returns = np.exp(np.cumsum(returns))
    running_max = np.maximum.accumulate(cum_returns)
    drawdown_series = (cum_returns - running_max) / running_max

    mdd = float(np.min(drawdown_series))
    mdd_idx = int(np.argmin(drawdown_series))

    # Find the peak before MDD trough
    peak_idx = int(np.argmax(cum_returns[:mdd_idx + 1]))
    duration = mdd_idx - peak_idx

    # Find recovery date (if any)
    recovery_idx = None
    for i in range(mdd_idx, len(cum_returns)):
        if cum_returns[i] >= cum_returns[peak_idx]:
            recovery_idx = i
            break

    recovery_duration = (recovery_idx - mdd_idx) if recovery_idx else None

    return {
        "max_drawdown": round(mdd, 6),
        "max_drawdown_pct": round(mdd * 100, 2),
        "peak_index": peak_idx,
        "trough_index": mdd_idx,
        "duration_days": duration,
        "recovery_days": recovery_duration,
        "drawdown_series": [round(float(d), 6) for d in drawdown_series],
    }


# ─── Beta & Alpha ─────────────────────────────────────────────────────────────

def compute_beta_alpha(
    returns: np.ndarray,
    market_returns: np.ndarray,
    rf: float = RISK_FREE_RATE,
) -> Dict[str, float]:
    """
    OLS regression: Rp - Rf = Alpha + Beta*(Rm - Rf) + ε

    Returns CAPM beta, Jensen's alpha, R-squared, and correlation.
    """
    if len(returns) != len(market_returns):
        min_len = min(len(returns), len(market_returns))
        returns = returns[-min_len:]
        market_returns = market_returns[-min_len:]

    daily_rf = rf / TRADING_DAYS
    excess_port = returns - daily_rf
    excess_mkt = market_returns - daily_rf

    slope, intercept, r_value, p_value, std_err = stats.linregress(excess_mkt, excess_port)

    alpha_annualized = float(intercept) * TRADING_DAYS
    capm_expected = rf + slope * (annualized_return(market_returns) - rf)

    return {
        "beta": round(float(slope), 4),
        "alpha": round(alpha_annualized, 4),
        "r_squared": round(float(r_value ** 2), 4),
        "correlation": round(float(r_value), 4),
        "p_value": round(float(p_value), 6),
        "capm_expected_return": round(capm_expected, 4),
    }


# ─── Value at Risk ────────────────────────────────────────────────────────────

def value_at_risk(
    returns: np.ndarray,
    confidence: float = 0.95,
    horizon: int = 1,
    method: str = "historical",
) -> float:
    """
    VaR at given confidence level over horizon days.

    Methods:
      - 'historical'   : Empirical percentile (non-parametric)
      - 'parametric'   : Normal distribution assumption
      - 'cornish_fisher': Adjusts for skewness and kurtosis (Cornish-Fisher expansion)
    """
    if method == "historical":
        scaled = returns * math.sqrt(horizon)
        return float(-np.percentile(scaled, (1 - confidence) * 100))

    mu = float(np.mean(returns)) * horizon
    sigma = float(np.std(returns, ddof=1)) * math.sqrt(horizon)

    if method == "parametric":
        z = stats.norm.ppf(1 - confidence)
        return float(-(mu + z * sigma))

    if method == "cornish_fisher":
        z = stats.norm.ppf(1 - confidence)
        skew = float(stats.skew(returns))
        kurt = float(stats.kurtosis(returns))
        z_cf = (z + (z ** 2 - 1) * skew / 6
                + (z ** 3 - 3 * z) * kurt / 24
                - (2 * z ** 3 - 5 * z) * skew ** 2 / 36)
        return float(-(mu + z_cf * sigma))

    raise ValueError(f"Unknown VaR method: {method}")


def conditional_var(returns: np.ndarray, confidence: float = 0.95) -> float:
    """
    CVaR (Expected Shortfall): mean of losses beyond VaR.
    ES_α = E[L | L > VaR_α]
    """
    cutoff = np.percentile(returns, (1 - confidence) * 100)
    tail = returns[returns <= cutoff]
    return float(-np.mean(tail)) if len(tail) > 0 else 0.0


# ─── Kelly Criterion ──────────────────────────────────────────────────────────

def kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> Dict[str, float]:
    """
    Kelly Criterion: optimal fraction of capital to bet.
    f* = (p*b - q) / b
    where p = win_rate, q = 1-p, b = avg_win/avg_loss

    Half-Kelly is commonly used in practice for risk management.
    Source: Kelly (1956) — Bell System Technical Journal.
    """
    if avg_loss == 0:
        return {"kelly_pct": 0.0, "half_kelly_pct": 0.0}
    q = 1 - win_rate
    b = avg_win / avg_loss
    kelly = (win_rate * b - q) / b
    return {
        "kelly_pct": round(max(0, kelly) * 100, 2),
        "half_kelly_pct": round(max(0, kelly / 2) * 100, 2),
        "win_rate": round(win_rate, 4),
        "avg_win_loss_ratio": round(b, 4),
        "interpretation": (
            f"Risk {min(kelly * 100, 25):.1f}% per trade (capped at 25% for safety)"
            if kelly > 0 else "Negative edge — do not trade this setup"
        ),
    }


def kelly_from_returns(returns: np.ndarray) -> Dict[str, float]:
    """Estimate Kelly from return distribution."""
    wins = returns[returns > 0]
    losses = returns[returns < 0]
    win_rate = len(wins) / len(returns) if len(returns) > 0 else 0
    avg_win = float(np.mean(wins)) if len(wins) > 0 else 0
    avg_loss = float(abs(np.mean(losses))) if len(losses) > 0 else 0
    return kelly_criterion(win_rate, avg_win, avg_loss)


# ─── Monte Carlo Simulation ───────────────────────────────────────────────────

def monte_carlo_gbm(
    current_price: float,
    expected_return: float,    # annualized
    volatility: float,         # annualized
    horizon_days: int = 252,
    n_simulations: int = 10_000,
    n_chart_paths: int = 100,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Geometric Brownian Motion Monte Carlo.

    dS = S(μ dt + σ √dt Z), Z ~ N(0,1)
    S(t+dt) = S(t) exp((μ - σ²/2)dt + σ√dt Z)

    Source: Black & Scholes (1973) — JPE.
    """
    if seed is not None:
        np.random.seed(seed)

    dt = 1.0 / TRADING_DAYS
    drift = (expected_return - 0.5 * volatility ** 2) * dt
    diffusion = volatility * math.sqrt(dt)

    # Shape: (n_simulations, horizon_days)
    Z = np.random.standard_normal((n_simulations, horizon_days))
    log_returns = drift + diffusion * Z
    price_paths = current_price * np.exp(np.cumsum(log_returns, axis=1))
    # Prepend current price
    price_paths = np.hstack([
        np.full((n_simulations, 1), current_price),
        price_paths,
    ])

    final_prices = price_paths[:, -1]

    # Statistics
    mean_price = float(np.mean(final_prices))
    std_price = float(np.std(final_prices, ddof=1))
    prob_profit = float(np.mean(final_prices > current_price))

    percentiles = {
        "p5": float(np.percentile(final_prices, 5)),
        "p10": float(np.percentile(final_prices, 10)),
        "p25": float(np.percentile(final_prices, 25)),
        "p50": float(np.percentile(final_prices, 50)),
        "p75": float(np.percentile(final_prices, 75)),
        "p90": float(np.percentile(final_prices, 90)),
        "p95": float(np.percentile(final_prices, 95)),
    }

    var_95 = float(np.percentile(final_prices, 5))
    var_99 = float(np.percentile(final_prices, 1))
    tail_95 = final_prices[final_prices <= var_95]
    tail_99 = final_prices[final_prices <= var_99]
    cvar_95 = float(np.mean(tail_95)) if len(tail_95) > 0 else var_95
    cvar_99 = float(np.mean(tail_99)) if len(tail_99) > 0 else var_99

    # Sample paths for charting
    indices = np.random.choice(n_simulations, size=min(n_chart_paths, n_simulations), replace=False)
    sample_paths = [[round(p, 2) for p in price_paths[i]] for i in indices]

    return {
        "simulations": n_simulations,
        "horizon_days": horizon_days,
        "current_price": round(current_price, 4),
        "mean_price": round(mean_price, 4),
        "std_price": round(std_price, 4),
        "var_95": round(var_95, 4),
        "var_99": round(var_99, 4),
        "cvar_95": round(cvar_95, 4),
        "cvar_99": round(cvar_99, 4),
        "probability_profit": round(prob_profit, 4),
        "expected_return_pct": round((mean_price / current_price - 1) * 100, 2),
        "percentiles": {k: round(v, 4) for k, v in percentiles.items()},
        "sample_paths": sample_paths,
    }


# ─── Full Quant Analysis ─────────────────────────────────────────────────────

def analyze_quant(
    ticker: str,
    prices: List[float],
    market_prices: Optional[List[float]] = None,
    rf: float = RISK_FREE_RATE,
) -> Dict[str, Any]:
    """Master function: compute all quant metrics for a stock."""
    if len(prices) < 30:
        return {"error": "Need at least 30 price observations"}

    returns = compute_returns(prices)
    ann_ret = annualized_return(returns)
    ann_vol = annualized_volatility(returns)

    beta_alpha = {}
    if market_prices and len(market_prices) >= len(prices):
        mkt_returns = compute_returns(market_prices[-len(prices):])
        if len(mkt_returns) == len(returns):
            beta_alpha = compute_beta_alpha(returns, mkt_returns, rf)

    beta = beta_alpha.get("beta", 1.0)
    mdd_data = max_drawdown(returns)
    kelly = kelly_from_returns(returns)

    # Monte Carlo — 1-year horizon
    mc = monte_carlo_gbm(
        current_price=prices[-1],
        expected_return=ann_ret,
        volatility=ann_vol,
        horizon_days=TRADING_DAYS,
        n_simulations=5_000,
        n_chart_paths=50,
    )

    # VaR/CVaR daily
    var_95_1d = value_at_risk(returns, 0.95, 1) * prices[-1]
    var_99_1d = value_at_risk(returns, 0.99, 1) * prices[-1]
    cvar_95_1d = conditional_var(returns, 0.95) * prices[-1]

    # Rolling beta (60-day window) vs market
    rolling_beta_series = []
    if market_prices and len(market_prices) >= len(prices):
        mkt_r = compute_returns(market_prices[-len(prices):])
        if len(mkt_r) >= 60:
            for i in range(60, len(returns)):
                port_w = returns[i - 60:i]
                mkt_w = mkt_r[i - 60:i]
                if len(mkt_w) == 60:
                    slope, *_ = stats.linregress(mkt_w, port_w)
                    rolling_beta_series.append({"index": i, "beta": round(float(slope), 4)})

    result = {
        "ticker": ticker,
        "period": f"{len(prices)} days",
        "annualized_return": round(ann_ret, 4),
        "annualized_return_pct": round(ann_ret * 100, 2),
        "annualized_volatility": round(ann_vol, 4),
        "annualized_volatility_pct": round(ann_vol * 100, 2),
        "sharpe_ratio": sharpe_ratio(returns, rf),
        "sortino_ratio": sortino_ratio(returns, rf),
        "calmar_ratio": calmar_ratio(returns),
        "omega_ratio": omega_ratio(returns),
        "max_drawdown": mdd_data["max_drawdown"],
        "max_drawdown_pct": mdd_data["max_drawdown_pct"],
        "max_drawdown_duration": mdd_data["duration_days"],
        "recovery_days": mdd_data["recovery_days"],
        "drawdown_series": mdd_data["drawdown_series"][-252:],
        "var_95_1d": round(var_95_1d, 2),
        "var_99_1d": round(var_99_1d, 2),
        "cvar_95_1d": round(cvar_95_1d, 2),
        "kelly_criterion": kelly,
        "monte_carlo": mc,
        "rolling_beta": rolling_beta_series[-60:],
        **beta_alpha,
    }

    if beta_alpha:
        result["treynor_ratio"] = treynor_ratio(returns, beta, rf)
        result["capm_expected_return"] = beta_alpha.get("capm_expected_return")

    return result
