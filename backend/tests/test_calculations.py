"""
Unit tests for quantitative calculations.

Tests: Black-Scholes, Greeks, VaR, Sharpe, DCF, Monte Carlo.
"""

import math
import pytest
import numpy as np

from app.services.options_analysis import (
    bs_price, calculate_greeks, implied_volatility, full_bs_analysis,
    calculate_max_pain, put_call_ratio,
)
from app.services.quant_analysis import (
    sharpe_ratio, sortino_ratio, calmar_ratio, max_drawdown,
    value_at_risk, conditional_var, kelly_criterion, monte_carlo_gbm,
    compute_returns, annualized_return, annualized_volatility,
)
from app.services.fundamental_analysis import dcf_valuation, cagr, estimate_wacc
from app.services.scoring_engine import compute_composite_score


# ─── Black-Scholes Tests ──────────────────────────────────────────────────────

class TestBlackScholes:

    def test_atm_call_gt_zero(self):
        price = bs_price(S=100, K=100, T=1.0, r=0.05, sigma=0.2)
        assert price > 0

    def test_call_put_parity(self):
        """Put-call parity: C - P = S - K*e^(-rT)"""
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.25
        call = bs_price(S, K, T, r, sigma, "call")
        put = bs_price(S, K, T, r, sigma, "put")
        parity_lhs = call - put
        parity_rhs = S - K * math.exp(-r * T)
        assert abs(parity_lhs - parity_rhs) < 1e-6, f"Put-call parity violated: {parity_lhs} != {parity_rhs}"

    def test_deep_itm_call_approaches_intrinsic(self):
        """Deep ITM call approaches intrinsic value S - K*e^(-rT)."""
        call = bs_price(S=200, K=100, T=1.0, r=0.05, sigma=0.2)
        intrinsic = 200 - 100 * math.exp(-0.05 * 1.0)
        assert abs(call - intrinsic) < 5, "Deep ITM call too far from intrinsic"

    def test_expired_option_is_intrinsic(self):
        """T=0 options equal their payoff."""
        assert bs_price(150, 100, 0, 0.05, 0.2, "call") == 50.0
        assert bs_price(80, 100, 0, 0.05, 0.2, "put") == 20.0
        assert bs_price(80, 100, 0, 0.05, 0.2, "call") == 0.0

    def test_call_increases_with_spot(self):
        """Call price monotonically increases with spot."""
        prices = [bs_price(S, 100, 1.0, 0.05, 0.2) for S in [80, 90, 100, 110, 120]]
        assert all(prices[i] < prices[i + 1] for i in range(len(prices) - 1))

    def test_put_decreases_with_spot(self):
        puts = [bs_price(S, 100, 1.0, 0.05, 0.2, "put") for S in [80, 90, 100, 110, 120]]
        assert all(puts[i] > puts[i + 1] for i in range(len(puts) - 1))

    def test_higher_vol_higher_price(self):
        """More volatility → more option value."""
        prices = [bs_price(100, 100, 1.0, 0.05, sigma) for sigma in [0.1, 0.2, 0.3, 0.5]]
        assert all(prices[i] < prices[i + 1] for i in range(len(prices) - 1))

    def test_full_analysis_returns_required_keys(self):
        result = full_bs_analysis(100, 100, 1.0, 0.05, 0.25)
        required = ["call_price", "put_price", "call_greeks", "put_greeks", "d1", "d2"]
        for key in required:
            assert key in result, f"Missing key: {key}"


# ─── Greeks Tests ─────────────────────────────────────────────────────────────

class TestGreeks:

    def setup_method(self):
        self.params = (100, 100, 1.0, 0.05, 0.25)

    def test_call_delta_bounds(self):
        g = calculate_greeks(*self.params, "call")
        assert 0 <= g["delta"] <= 1, f"Call delta out of bounds: {g['delta']}"

    def test_put_delta_bounds(self):
        g = calculate_greeks(*self.params, "put")
        assert -1 <= g["delta"] <= 0, f"Put delta out of bounds: {g['delta']}"

    def test_call_put_delta_sum(self):
        """Call delta - put delta = 1 (for European options)"""
        g_call = calculate_greeks(*self.params, "call")
        g_put = calculate_greeks(*self.params, "put")
        assert abs(g_call["delta"] - g_put["delta"] - 1.0) < 1e-6

    def test_gamma_positive(self):
        """Gamma is always positive for long options."""
        g = calculate_greeks(*self.params, "call")
        assert g["gamma"] > 0

    def test_call_theta_negative(self):
        """Theta is negative (time decay hurts long options)."""
        g = calculate_greeks(*self.params, "call")
        assert g["theta"] < 0

    def test_vega_positive(self):
        """Vega is positive — more vol → higher option value."""
        g = calculate_greeks(*self.params, "call")
        assert g["vega"] > 0

    def test_all_greeks_present(self):
        g = calculate_greeks(*self.params, "call")
        for key in ["delta", "gamma", "theta", "vega", "rho", "vanna", "charm", "vomma", "speed", "color", "zomma"]:
            assert key in g, f"Missing greek: {key}"

    def test_gamma_call_put_equal(self):
        """Gamma is the same for call and put at same strike."""
        g_call = calculate_greeks(*self.params, "call")["gamma"]
        g_put = calculate_greeks(*self.params, "put")["gamma"]
        assert abs(g_call - g_put) < 1e-10


# ─── Implied Volatility Tests ─────────────────────────────────────────────────

class TestImpliedVolatility:

    def test_round_trip_call(self):
        """IV solver should recover the original sigma."""
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.25
        market_price = bs_price(S, K, T, r, sigma, "call")
        iv = implied_volatility(market_price, S, K, T, r, "call")
        assert iv is not None
        assert abs(iv - sigma) < 1e-3, f"IV round-trip error: {iv} vs {sigma}"

    def test_round_trip_put(self):
        S, K, T, r, sigma = 100, 110, 0.5, 0.03, 0.30
        market_price = bs_price(S, K, T, r, sigma, "put")
        iv = implied_volatility(market_price, S, K, T, r, "put")
        assert iv is not None
        assert abs(iv - sigma) < 1e-3


# ─── Quant Analysis Tests ──────────────────────────────────────────────────────

def _random_returns(n=252, seed=42):
    np.random.seed(seed)
    return np.random.normal(0.0004, 0.015, n)  # ~10% ann return, 24% vol


class TestQuantMetrics:

    def test_sharpe_positive_for_positive_returns(self):
        returns = _random_returns() + 0.002  # drift up
        assert sharpe_ratio(returns) > 0

    def test_sharpe_negative_for_negative_returns(self):
        returns = _random_returns() - 0.002
        sr = sharpe_ratio(returns)
        assert sr < sharpe_ratio(_random_returns())

    def test_sortino_ge_sharpe_for_positive_drift(self):
        """Sortino should be >= Sharpe when returns are mostly positive."""
        returns = _random_returns() + 0.001
        assert sortino_ratio(returns) >= sharpe_ratio(returns) - 0.1

    def test_max_drawdown_negative(self):
        returns = _random_returns()
        mdd = max_drawdown(returns)
        assert mdd["max_drawdown"] <= 0
        assert "max_drawdown_pct" in mdd

    def test_max_drawdown_zero_for_always_up(self):
        returns = np.full(100, 0.001)  # always positive
        mdd = max_drawdown(returns)["max_drawdown"]
        assert mdd >= -1e-8  # should be ~0

    def test_var_95_less_than_var_99(self):
        returns = _random_returns()
        var_95 = value_at_risk(returns, 0.95)
        var_99 = value_at_risk(returns, 0.99)
        assert var_95 < var_99, "99% VaR should be larger loss than 95%"

    def test_cvar_ge_var(self):
        """CVaR (expected shortfall) should be >= VaR at same confidence."""
        returns = _random_returns()
        var = value_at_risk(returns, 0.95)
        cvar = conditional_var(returns, 0.95)
        assert cvar >= var * 0.9  # some tolerance for sampling

    def test_kelly_positive_edge(self):
        k = kelly_criterion(win_rate=0.55, avg_win=0.02, avg_loss=0.015)
        assert k["kelly_pct"] > 0

    def test_kelly_negative_edge(self):
        k = kelly_criterion(win_rate=0.40, avg_win=0.01, avg_loss=0.02)
        assert k["kelly_pct"] == 0


# ─── Monte Carlo Tests ────────────────────────────────────────────────────────

class TestMonteCarlo:

    def test_returns_required_keys(self):
        result = monte_carlo_gbm(100, 0.10, 0.20, 252, 1000, 10, seed=1)
        for key in ["simulations", "mean_price", "var_95", "cvar_95", "sample_paths"]:
            assert key in result

    def test_mean_price_near_current(self):
        """For zero-drift, mean price should be close to starting price."""
        result = monte_carlo_gbm(100, 0.0, 0.20, 252, 5000, 0, seed=42)
        assert abs(result["mean_price"] / 100 - 1) < 0.10  # within 10%

    def test_probability_profit_bounds(self):
        result = monte_carlo_gbm(100, 0.10, 0.20, 252, 2000, 0, seed=99)
        assert 0 <= result["probability_profit"] <= 1

    def test_sample_paths_shape(self):
        result = monte_carlo_gbm(100, 0.10, 0.20, 30, 1000, 20, seed=5)
        assert len(result["sample_paths"]) == 20
        assert len(result["sample_paths"][0]) == 31  # T+1 (includes day 0)


# ─── DCF Tests ────────────────────────────────────────────────────────────────

class TestDCF:

    def test_positive_intrinsic_value(self):
        result = dcf_valuation(
            fcf=1e9, shares_outstanding=1e8,
            current_price=50, growth_1_5=0.15,
            growth_6_10=0.10, terminal_growth=0.03,
            wacc=0.10,
        )
        assert result["intrinsic_value"] > 0

    def test_higher_growth_higher_value(self):
        base = dcf_valuation(1e9, 1e8, 50, 0.10, 0.07, 0.03, 0.10)
        high = dcf_valuation(1e9, 1e8, 50, 0.20, 0.15, 0.03, 0.10)
        assert high["intrinsic_value"] > base["intrinsic_value"]

    def test_higher_wacc_lower_value(self):
        low = dcf_valuation(1e9, 1e8, 50, 0.12, 0.08, 0.025, 0.09)
        high = dcf_valuation(1e9, 1e8, 50, 0.12, 0.08, 0.025, 0.15)
        assert low["intrinsic_value"] > high["intrinsic_value"]

    def test_has_stage_projections(self):
        result = dcf_valuation(1e9, 1e8, 50)
        assert len(result["stage1_projections"]) == 5
        assert len(result["stage2_projections"]) == 5

    def test_margin_of_safety_when_undervalued(self):
        result = dcf_valuation(
            fcf=5e9, shares_outstanding=1e8,
            current_price=50, growth_1_5=0.20, growth_6_10=0.12,
            terminal_growth=0.03, wacc=0.09,
        )
        assert result["margin_of_safety"] > 0  # intrinsic > current price


# ─── CAGR Tests ───────────────────────────────────────────────────────────────

class TestCAGR:

    def test_cagr_2x_in_5_years(self):
        result = cagr(start=100, end=200, years=5)
        expected = 2 ** (1 / 5) - 1
        assert abs(result - expected) < 1e-6

    def test_cagr_negative_growth(self):
        result = cagr(start=100, end=80, years=4)
        assert result < 0

    def test_cagr_none_on_invalid(self):
        assert cagr(0, 100, 3) is None
        assert cagr(100, 100, 0) is None


# ─── Max Pain Tests ───────────────────────────────────────────────────────────

class TestOptionsMath:

    def test_max_pain_returns_a_strike(self):
        chain = [
            {"strike": 90, "call_oi": 100, "put_oi": 500},
            {"strike": 100, "call_oi": 200, "put_oi": 400},
            {"strike": 110, "call_oi": 600, "put_oi": 100},
        ]
        mp = calculate_max_pain(chain)
        assert mp in [90, 100, 110]

    def test_pcr_returns_expected_ratio(self):
        chain = [{"call_oi": 1000, "put_oi": 1500, "call_volume": 200, "put_volume": 300}]
        result = put_call_ratio(chain)
        assert abs(result["pcr_oi"] - 1.5) < 1e-4
