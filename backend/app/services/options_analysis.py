"""
Options analysis service.

Implements Black-Scholes pricing, complete Greeks (Δ Γ Θ ν ρ + higher-order),
implied volatility via Newton-Raphson, IV rank/percentile, max-pain,
gamma exposure (GEX), and volatility surface construction.
"""

import logging
import math
from typing import Optional, Dict, Any, List, Tuple

import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


# ─── Black-Scholes Core ──────────────────────────────────────────────────────

def _d1d2(S: float, K: float, T: float, r: float, sigma: float) -> Tuple[float, float]:
    """Compute d1 and d2 for Black-Scholes."""
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        raise ValueError("Invalid parameters for Black-Scholes")
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return d1, d2


def bs_price(S: float, K: float, T: float, r: float, sigma: float, option_type: str = "call") -> float:
    """
    Black-Scholes European option price.

    Parameters
    ----------
    S     : Spot price
    K     : Strike price
    T     : Time to expiry in years
    r     : Continuously compounded risk-free rate
    sigma : Annualized implied volatility (decimal)
    option_type : 'call' or 'put'

    Returns
    -------
    Theoretical option price
    """
    if T <= 0:
        return max(S - K, 0) if option_type == "call" else max(K - S, 0)

    d1, d2 = _d1d2(S, K, T, r, sigma)
    if option_type == "call":
        return S * stats.norm.cdf(d1) - K * math.exp(-r * T) * stats.norm.cdf(d2)
    else:
        return K * math.exp(-r * T) * stats.norm.cdf(-d2) - S * stats.norm.cdf(-d1)


def calculate_greeks(S: float, K: float, T: float, r: float, sigma: float, option_type: str = "call") -> Dict[str, float]:
    """
    Compute full set of option Greeks.

    First-order  : Delta, Vega, Theta, Rho
    Second-order : Gamma, Vanna, Charm, Vomma
    Third-order  : Speed, Color, Zomma

    Formulae reference: Hull — Options, Futures and Other Derivatives (10th ed.)
    """
    if T <= 0 or sigma <= 0:
        return _zero_greeks()

    d1, d2 = _d1d2(S, K, T, r, sigma)
    phi_d1 = stats.norm.pdf(d1)      # N'(d1)
    phi_d2 = stats.norm.pdf(d2)      # N'(d2)
    N_d1 = stats.norm.cdf(d1)
    N_d2 = stats.norm.cdf(d2)
    sqrt_T = math.sqrt(T)
    exp_rT = math.exp(-r * T)

    # Delta
    if option_type == "call":
        delta = N_d1
    else:
        delta = N_d1 - 1.0

    # Gamma  (same for call and put)
    gamma = phi_d1 / (S * sigma * sqrt_T)

    # Theta  (per calendar day, not per year)
    theta_common = -(S * phi_d1 * sigma) / (2 * sqrt_T)
    if option_type == "call":
        theta = (theta_common - r * K * exp_rT * N_d2) / 365.0
    else:
        theta = (theta_common + r * K * exp_rT * stats.norm.cdf(-d2)) / 365.0

    # Vega   (per 1% change in sigma)
    vega = S * phi_d1 * sqrt_T / 100.0

    # Rho    (per 1% change in rate)
    if option_type == "call":
        rho = K * T * exp_rT * N_d2 / 100.0
    else:
        rho = -K * T * exp_rT * stats.norm.cdf(-d2) / 100.0

    # Vanna  = d(Delta)/d(sigma) = -phi(d1) * d2 / sigma
    vanna = -phi_d1 * d2 / sigma

    # Charm  = d(Delta)/d(t) = -phi(d1) * [2rT - d2*sigma*sqrtT] / [2T*sigma*sqrtT]
    charm_num = 2.0 * r * T - d2 * sigma * sqrt_T
    charm = -phi_d1 * charm_num / (2.0 * T * sigma * sqrt_T)
    if option_type == "put":
        charm = charm  # same formula, sign embedded in delta context

    # Vomma  = d(Vega)/d(sigma) = Vega * d1 * d2 / sigma  (per 1% change)
    vomma = vega * d1 * d2 / sigma

    # Speed  = d(Gamma)/dS = -Gamma/S * (d1/(sigma*sqrtT) + 1)
    speed = -gamma / S * (d1 / (sigma * sqrt_T) + 1.0)

    # Color  = d(Gamma)/d(t) — "gamma decay"
    color = -gamma / (2.0 * T) * (1.0 + d1 * (2.0 * r * T - d2 * sigma * sqrt_T) / (sigma * sqrt_T))

    # Zomma  = d(Gamma)/d(sigma) = Gamma * (d1*d2 - 1) / sigma
    zomma = gamma * (d1 * d2 - 1.0) / sigma

    return {
        "delta": round(delta, 6),
        "gamma": round(gamma, 8),
        "theta": round(theta, 6),
        "vega": round(vega, 6),
        "rho": round(rho, 6),
        "vanna": round(vanna, 8),
        "charm": round(charm, 8),
        "vomma": round(vomma, 8),
        "speed": round(speed, 10),
        "color": round(color, 10),
        "zomma": round(zomma, 10),
    }


def _zero_greeks() -> Dict[str, float]:
    return {k: 0.0 for k in ["delta", "gamma", "theta", "vega", "rho", "vanna", "charm", "vomma", "speed", "color", "zomma"]}


def full_bs_analysis(S: float, K: float, T: float, r: float, sigma: float) -> Dict[str, Any]:
    """Return prices + greeks for both call and put."""
    d1, d2 = _d1d2(S, K, T, r, sigma)
    return {
        "call_price": round(bs_price(S, K, T, r, sigma, "call"), 4),
        "put_price": round(bs_price(S, K, T, r, sigma, "put"), 4),
        "call_greeks": calculate_greeks(S, K, T, r, sigma, "call"),
        "put_greeks": calculate_greeks(S, K, T, r, sigma, "put"),
        "d1": round(d1, 6),
        "d2": round(d2, 6),
        "stock_price": S,
        "strike": K,
        "time_to_expiry": T,
        "risk_free_rate": r,
        "volatility": sigma,
        "intrinsic_value_call": round(max(S - K, 0), 4),
        "intrinsic_value_put": round(max(K - S, 0), 4),
        "time_value_call": round(bs_price(S, K, T, r, sigma, "call") - max(S - K, 0), 4),
        "moneyness": round(S / K, 4),
    }


# ─── Implied Volatility ───────────────────────────────────────────────────────

def implied_volatility(
    market_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    option_type: str = "call",
    tol: float = 1e-6,
    max_iter: int = 100,
) -> Optional[float]:
    """
    Newton-Raphson solver for implied volatility.

    Returns IV as a decimal (e.g., 0.30 for 30%), or None if no solution.
    """
    if T <= 0 or market_price <= 0:
        return None

    intrinsic = max(S - K, 0) if option_type == "call" else max(K - S, 0)
    if market_price < intrinsic - 1e-4:
        return None

    sigma = 0.3  # initial guess
    for _ in range(max_iter):
        try:
            price = bs_price(S, K, T, r, sigma, option_type)
            d1, _ = _d1d2(S, K, T, r, sigma)
            vega_raw = S * stats.norm.pdf(d1) * math.sqrt(T)
            if abs(vega_raw) < 1e-10:
                break
            sigma -= (price - market_price) / vega_raw
            sigma = max(1e-6, min(sigma, 20.0))  # clamp to [0.0001, 2000%]
            if abs(bs_price(S, K, T, r, sigma, option_type) - market_price) < tol:
                return round(sigma, 6)
        except Exception:
            break
    return round(sigma, 6) if 0 < sigma < 20 else None


# ─── Volatility Metrics ───────────────────────────────────────────────────────

def historical_volatility(close_prices: List[float], period: int = 30) -> float:
    """Annualized historical volatility from daily log-returns."""
    if len(close_prices) < period + 1:
        period = len(close_prices) - 1
    prices = np.array(close_prices[-period - 1:])
    log_returns = np.diff(np.log(prices))
    return float(np.std(log_returns, ddof=1) * math.sqrt(252))


def realized_volatility(close_prices: List[float], period: int = 21) -> float:
    """21-day realized volatility (Parkinson estimator) — uses close-to-close."""
    return historical_volatility(close_prices, period)


def iv_rank(current_iv: float, iv_history: List[float]) -> float:
    """
    IV Rank: where is current IV relative to its 52-week range?
    Returns 0–100.
    """
    if not iv_history:
        return 50.0
    iv_high = max(iv_history)
    iv_low = min(iv_history)
    if iv_high == iv_low:
        return 50.0
    return round((current_iv - iv_low) / (iv_high - iv_low) * 100, 2)


def iv_percentile(current_iv: float, iv_history: List[float]) -> float:
    """
    IV Percentile: fraction of past days where IV was lower than current IV.
    Returns 0–100.
    """
    if not iv_history:
        return 50.0
    return round(float(stats.percentileofscore(iv_history, current_iv)), 2)


# ─── Max Pain ─────────────────────────────────────────────────────────────────

def calculate_max_pain(chain: List[Dict[str, Any]]) -> Optional[float]:
    """
    Max Pain: strike at which aggregate dollar loss of ALL option buyers is maximised.
    (Equivalently, where option writers/dealers profit most.)

    For each candidate strike P:
      Pain = Σ_calls OI_k × max(P - K_k, 0) + Σ_puts OI_k × max(K_k - P, 0)
    """
    strikes = [row["strike"] for row in chain if "strike" in row]
    if not strikes:
        return None

    pain = {}
    for P in strikes:
        call_pain = sum(
            (row.get("call_oi") or 0) * max(P - row["strike"], 0)
            for row in chain
        )
        put_pain = sum(
            (row.get("put_oi") or 0) * max(row["strike"] - P, 0)
            for row in chain
        )
        pain[P] = call_pain + put_pain

    return float(min(pain, key=pain.get))


# ─── Gamma Exposure ───────────────────────────────────────────────────────────

def calculate_gex(
    chain: List[Dict[str, Any]],
    spot: float,
    lot_size: int = 100,
) -> Dict[str, Any]:
    """
    Dealer Gamma Exposure (GEX).

    GEX at strike K = (call_OI - put_OI) × Gamma × lot_size × spot² × 0.01
    Total GEX = Σ GEX_K over all strikes.

    Positive GEX → dealers are long gamma → stabilising.
    Negative GEX → dealers short gamma → destabilising / potential squeeze.
    """
    total_gex = 0.0
    gex_by_strike = []
    r = 0.05

    for row in chain:
        K = row.get("strike")
        T = (row.get("days_to_expiry") or 30) / 365.0
        iv = row.get("call_iv") or row.get("put_iv") or 0.3
        if not K or T <= 0 or iv <= 0:
            continue
        try:
            g = calculate_greeks(spot, K, T, r, iv, "call")["gamma"]
            call_oi = row.get("call_oi") or 0
            put_oi = row.get("put_oi") or 0
            net_oi = call_oi - put_oi
            gex_k = net_oi * g * lot_size * (spot ** 2) * 0.01
            total_gex += gex_k
            gex_by_strike.append({"strike": K, "gex": round(gex_k / 1e6, 4)})  # in $M
        except Exception:
            continue

    squeeze_score = min(100.0, max(0.0, abs(total_gex) / 1e9 * 10)) if total_gex < 0 else 0.0

    return {
        "total_gex": round(total_gex / 1e9, 4),  # in $B
        "gex_by_strike": gex_by_strike,
        "dealer_positioning": "long_gamma" if total_gex > 0 else "short_gamma",
        "squeeze_risk": "high" if total_gex < -1e9 else "moderate" if total_gex < 0 else "low",
        "gamma_squeeze_score": round(squeeze_score, 2),
    }


# ─── Put/Call Ratio ───────────────────────────────────────────────────────────

def put_call_ratio(chain: List[Dict[str, Any]]) -> Dict[str, float]:
    total_call_oi = sum(row.get("call_oi") or 0 for row in chain)
    total_put_oi = sum(row.get("put_oi") or 0 for row in chain)
    total_call_vol = sum(row.get("call_volume") or 0 for row in chain)
    total_put_vol = sum(row.get("put_volume") or 0 for row in chain)

    pcr_oi = round(total_put_oi / total_call_oi, 4) if total_call_oi else 0
    pcr_vol = round(total_put_vol / total_call_vol, 4) if total_call_vol else 0

    return {
        "pcr_oi": pcr_oi,
        "pcr_volume": pcr_vol,
        "total_call_oi": total_call_oi,
        "total_put_oi": total_put_oi,
        "signal": "bullish" if pcr_oi < 0.7 else "bearish" if pcr_oi > 1.3 else "neutral",
        "interpretation": (
            "Bullish sentiment — more calls than puts"
            if pcr_oi < 0.7 else
            "Bearish sentiment — elevated put buying"
            if pcr_oi > 1.3 else
            "Neutral sentiment"
        ),
    }


# ─── Volatility Skew ──────────────────────────────────────────────────────────

def compute_vol_skew(chain: List[Dict[str, Any]], spot: float) -> List[Dict[str, float]]:
    """
    Compute volatility smile — IV at each strike as % of spot (moneyness).
    """
    skew = []
    for row in chain:
        K = row.get("strike")
        iv = row.get("call_iv") or row.get("put_iv")
        if K and iv and iv > 0:
            skew.append({
                "strike": K,
                "moneyness": round(K / spot, 4),
                "iv": round(float(iv) * 100, 2),
                "log_moneyness": round(math.log(K / spot), 4),
            })
    return sorted(skew, key=lambda x: x["strike"])


def compute_vol_surface(
    chains: Dict[str, List[Dict[str, Any]]],
    spot: float,
) -> List[Dict[str, Any]]:
    """
    Build a 2-D volatility surface (strike × expiry → IV).
    chains: {expiry_str: chain_list}
    """
    surface = []
    for expiry, chain in chains.items():
        for row in chain:
            K = row.get("strike")
            iv = row.get("call_iv") or row.get("put_iv")
            dte = row.get("days_to_expiry", 30)
            if K and iv and iv > 0:
                surface.append({
                    "expiry": expiry,
                    "strike": K,
                    "moneyness": round(K / spot, 4),
                    "dte": dte,
                    "iv": round(float(iv) * 100, 2),
                })
    return surface


# ─── Complete Options Analysis ────────────────────────────────────────────────

def analyze_options(
    ticker: str,
    spot: float,
    chain: List[Dict[str, Any]],
    close_prices: List[float],
    expiry_dates: List[str],
    selected_expiry: str,
) -> Dict[str, Any]:
    """Aggregate all options metrics for a ticker."""

    hv_30 = historical_volatility(close_prices, 30) if len(close_prices) > 31 else None
    hv_60 = historical_volatility(close_prices, 60) if len(close_prices) > 61 else None

    # Estimate current ATM IV
    atm_rows = sorted(chain, key=lambda x: abs(x.get("strike", 0) - spot))
    current_atm_iv = None
    if atm_rows:
        best = atm_rows[0]
        current_atm_iv = best.get("call_iv") or best.get("put_iv")

    # Build IV history from rolling HV for rank/percentile (proxy when historical IV not stored)
    iv_hist = [historical_volatility(close_prices[max(0, i-30):i]) for i in range(60, len(close_prices))]

    pcr = put_call_ratio(chain)
    max_pain = calculate_max_pain(chain)
    gex_data = calculate_gex(chain, spot)
    skew = compute_vol_skew(chain, spot)

    ivr = iv_rank(current_atm_iv or (hv_30 or 0.3), iv_hist) if iv_hist else None
    ivp = iv_percentile(current_atm_iv or (hv_30 or 0.3), iv_hist) if iv_hist else None

    return {
        "ticker": ticker,
        "spot_price": spot,
        "put_call_ratio": pcr,
        "iv_rank": ivr,
        "iv_percentile": ivp,
        "current_iv": round(float(current_atm_iv) * 100, 2) if current_atm_iv else None,
        "historical_vol_30d": round(hv_30 * 100, 2) if hv_30 else None,
        "historical_vol_60d": round(hv_60 * 100, 2) if hv_60 else None,
        "realized_vol": round(hv_30 * 100, 2) if hv_30 else None,
        "max_pain": max_pain,
        "gamma_exposure": gex_data["total_gex"],
        "gamma_squeeze_score": gex_data["gamma_squeeze_score"],
        "dealer_positioning": gex_data["dealer_positioning"],
        "squeeze_risk": gex_data["squeeze_risk"],
        "gex_by_strike": gex_data["gex_by_strike"],
        "option_chain": chain,
        "expiry_dates": expiry_dates,
        "selected_expiry": selected_expiry,
        "vol_skew": skew,
    }
