"""
Fundamental analysis service.

Parses financial statements, computes ratios, and runs a multi-stage DCF
valuation with WACC estimation and margin of safety calculation.
"""

import logging
import math
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

WACC_DEFAULT = 0.10
TERMINAL_GROWTH_DEFAULT = 0.025
TAX_RATE_DEFAULT = 0.21


# ─── Statement Parsing ────────────────────────────────────────────────────────

def _get_value(stmt: List[Dict[str, Any]], field_aliases: List[str], year_idx: int = 0) -> Optional[float]:
    """Extract a metric from parsed financial statement rows."""
    if not stmt or year_idx >= len(stmt):
        return None
    row = stmt[year_idx]
    for alias in field_aliases:
        for k, v in row.items():
            if alias.lower() in k.lower():
                try:
                    return float(v)
                except (TypeError, ValueError):
                    pass
    return None


def parse_income_statements(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    for i, row in enumerate(raw[:5]):
        year = str(row.get("date", f"Y{i+1}"))[:7]
        revenue = _get_value([row], ["total_revenue", "totalrevenue", "revenue"])
        gross = _get_value([row], ["gross_profit", "grossprofit"])
        op_income = _get_value([row], ["ebit", "operating_income", "operatingincome"])
        net_income = _get_value([row], ["net_income", "netincome"])
        ebitda = _get_value([row], ["ebitda"])
        eps = _get_value([row], ["basic_eps", "diluted_eps", "eps"])
        results.append({
            "year": year,
            "revenue": revenue,
            "gross_profit": gross,
            "operating_income": op_income,
            "net_income": net_income,
            "ebitda": ebitda,
            "eps": eps,
            "gross_margin": round(gross / revenue * 100, 2) if gross and revenue else None,
            "operating_margin": round(op_income / revenue * 100, 2) if op_income and revenue else None,
            "net_margin": round(net_income / revenue * 100, 2) if net_income and revenue else None,
        })
    return results


def parse_balance_sheets(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    for i, row in enumerate(raw[:5]):
        year = str(row.get("date", f"Y{i+1}"))[:7]
        total_assets = _get_value([row], ["total_assets", "totalassets"])
        total_liab = _get_value([row], ["total_liabilities", "totalliabilitiesnetminority"])
        equity = _get_value([row], ["stockholders_equity", "total_equity", "totalequitygrossmino"])
        cash = _get_value([row], ["cash_and_cash_equivalents", "cashandcashequivalents", "cash"])
        debt = _get_value([row], ["long_term_debt", "total_debt", "longtermdebt"])
        current_assets = _get_value([row], ["current_assets", "currentassets"])
        current_liab = _get_value([row], ["current_liabilities", "currentliabilities"])
        shares = _get_value([row], ["ordinary_shares_number", "sharesoutstanding"])
        bvps = (equity / shares) if equity and shares and shares > 0 else None
        results.append({
            "year": year,
            "total_assets": total_assets,
            "total_liabilities": total_liab,
            "total_equity": equity,
            "cash": cash,
            "total_debt": debt,
            "current_assets": current_assets,
            "current_liabilities": current_liab,
            "book_value_per_share": round(bvps, 4) if bvps else None,
            "debt_to_equity": round(debt / equity, 4) if debt and equity else None,
            "current_ratio": round(current_assets / current_liab, 4) if current_assets and current_liab else None,
        })
    return results


def parse_cash_flows(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    for i, row in enumerate(raw[:5]):
        year = str(row.get("date", f"Y{i+1}"))[:7]
        op_cf = _get_value([row], ["operating_cash_flow", "cash_from_operations", "operatingcashflow"])
        capex = _get_value([row], ["capital_expenditure", "capex", "capitalexpenditure"])
        fcf = op_cf + capex if op_cf and capex else (op_cf if op_cf else None)
        dividends = _get_value([row], ["dividends_paid", "cash_dividends_paid"])
        results.append({
            "year": year,
            "operating_cash_flow": op_cf,
            "capex": capex,
            "free_cash_flow": fcf,
            "dividends_paid": dividends,
        })
    return results


# ─── Growth Rate CAGR ────────────────────────────────────────────────────────

def cagr(start: Optional[float], end: Optional[float], years: int) -> Optional[float]:
    """Compound Annual Growth Rate over n years."""
    if not start or not end or years <= 0 or start <= 0:
        return None
    return round((end / start) ** (1 / years) - 1, 4)


# ─── Financial Ratios ────────────────────────────────────────────────────────

def compute_ratios(income: List[Dict], balance: List[Dict], cashflow: List[Dict]) -> Dict[str, Any]:
    if not income or not balance:
        return {}

    inc = income[0]
    bal = balance[0]
    cf = cashflow[0] if cashflow else {}

    revenue = inc.get("revenue")
    net_income = inc.get("net_income")
    ebitda = inc.get("ebitda")
    op_income = inc.get("operating_income")
    equity = bal.get("total_equity")
    assets = bal.get("total_assets")
    debt = bal.get("total_debt")
    cash = bal.get("cash")
    current_assets = bal.get("current_assets")
    current_liab = bal.get("current_liabilities")
    net_debt = (debt - cash) if debt and cash else debt
    fcf = cf.get("free_cash_flow")

    result = {}

    # Profitability
    if equity and net_income:
        result["roe"] = round(net_income / equity, 4)
    if assets and net_income:
        result["roa"] = round(net_income / assets, 4)
    if revenue and net_income:
        result["net_margin"] = round(net_income / revenue, 4)
    if revenue and op_income:
        result["operating_margin"] = round(op_income / revenue, 4)

    # ROCE = EBIT / (Total Assets - Current Liabilities)
    if op_income and assets and current_liab:
        capital_employed = assets - current_liab
        result["roce"] = round(op_income / capital_employed, 4) if capital_employed else None

    # Leverage
    if debt and equity:
        result["debt_to_equity"] = round(debt / equity, 4)
    if ebitda and debt:
        result["debt_to_ebitda"] = round(net_debt / ebitda, 4) if net_debt else None
    if ebitda and debt:
        # Interest coverage requires interest expense — proxy with op_income/ebitda
        result["interest_coverage"] = round(ebitda / max(debt * 0.05, 1), 2)

    # Liquidity
    if current_assets and current_liab:
        result["current_ratio"] = round(current_assets / current_liab, 4)
        inventory = current_assets * 0.3  # proxy
        result["quick_ratio"] = round((current_assets - inventory) / current_liab, 4)

    # Cash flow
    if fcf:
        result["free_cash_flow"] = fcf

    # Growth
    if len(income) >= 4:
        rev_3y_cagr = cagr(income[3].get("revenue"), inc.get("revenue"), 3)
        eps_3y_cagr = cagr(income[3].get("eps"), inc.get("eps"), 3)
        result["revenue_cagr_3y"] = rev_3y_cagr
        result["eps_cagr_3y"] = eps_3y_cagr

    if len(cashflow) >= 4:
        fcf_3y_cagr = cagr(cashflow[3].get("free_cash_flow"), fcf, 3)
        result["fcf_cagr_3y"] = fcf_3y_cagr

    return result


# ─── WACC Estimation ──────────────────────────────────────────────────────────

def estimate_wacc(
    equity_value: Optional[float],
    debt_value: Optional[float],
    cost_of_equity: float,
    cost_of_debt: float = 0.05,
    tax_rate: float = TAX_RATE_DEFAULT,
) -> float:
    """
    WACC = (E/V)*Re + (D/V)*Rd*(1-T)

    Cost of Equity estimated via CAPM: Re = Rf + Beta*(Rm - Rf)
    """
    if not equity_value or not debt_value:
        return WACC_DEFAULT
    V = equity_value + debt_value
    if V == 0:
        return WACC_DEFAULT
    E = equity_value / V
    D = debt_value / V
    return round(E * cost_of_equity + D * cost_of_debt * (1 - tax_rate), 4)


# ─── DCF Valuation ────────────────────────────────────────────────────────────

def dcf_valuation(
    fcf: float,
    shares_outstanding: float,
    current_price: float,
    growth_1_5: float = 0.10,
    growth_6_10: float = 0.06,
    terminal_growth: float = TERMINAL_GROWTH_DEFAULT,
    wacc: float = WACC_DEFAULT,
    net_debt: float = 0.0,
) -> Dict[str, Any]:
    """
    Two-stage DCF model with explicit 10-year forecast + terminal value.

    Stage 1 (Years 1-5): High growth phase
    Stage 2 (Years 6-10): Transition to mature growth
    Terminal Value: Gordon Growth Model — TV = FCF_10 × (1+g) / (WACC-g)

    Source: Damodaran — Investment Valuation (3rd ed.)
    """
    if wacc <= terminal_growth:
        wacc = terminal_growth + 0.02  # ensure WACC > g

    stage1_fcfs = []
    pv_stage1 = 0.0
    fcf_t = fcf
    for year in range(1, 6):
        fcf_t *= (1 + growth_1_5)
        pv = fcf_t / (1 + wacc) ** year
        stage1_fcfs.append({
            "year": year,
            "fcf": round(fcf_t, 2),
            "pv": round(pv, 2),
        })
        pv_stage1 += pv

    stage2_fcfs = []
    pv_stage2 = 0.0
    for year in range(6, 11):
        fcf_t *= (1 + growth_6_10)
        pv = fcf_t / (1 + wacc) ** year
        stage2_fcfs.append({
            "year": year,
            "fcf": round(fcf_t, 2),
            "pv": round(pv, 2),
        })
        pv_stage2 += pv

    # Terminal value at end of year 10
    tv = fcf_t * (1 + terminal_growth) / (wacc - terminal_growth)
    tv_pv = tv / (1 + wacc) ** 10

    enterprise_value = pv_stage1 + pv_stage2 + tv_pv
    equity_value = enterprise_value - net_debt
    intrinsic_per_share = equity_value / shares_outstanding if shares_outstanding > 0 else 0

    margin_of_safety = (intrinsic_per_share - current_price) / intrinsic_per_share if intrinsic_per_share > 0 else 0
    upside = (intrinsic_per_share - current_price) / current_price if current_price > 0 else 0

    return {
        "intrinsic_value": round(intrinsic_per_share, 4),
        "current_price": round(current_price, 4),
        "margin_of_safety": round(margin_of_safety, 4),
        "upside_downside": round(upside, 4),
        "upside_pct": round(upside * 100, 2),
        "enterprise_value": round(enterprise_value, 2),
        "equity_value": round(equity_value, 2),
        "stage1_value": round(pv_stage1, 2),
        "stage2_value": round(pv_stage2, 2),
        "terminal_value": round(tv, 2),
        "terminal_value_pv": round(tv_pv, 2),
        "tv_pct_of_ev": round(tv_pv / enterprise_value * 100, 2) if enterprise_value > 0 else 0,
        "wacc": round(wacc, 4),
        "terminal_growth_rate": round(terminal_growth, 4),
        "assumptions": {
            "growth_1_5yr": round(growth_1_5 * 100, 1),
            "growth_6_10yr": round(growth_6_10 * 100, 1),
            "terminal_growth_pct": round(terminal_growth * 100, 1),
            "wacc_pct": round(wacc * 100, 1),
        },
        "stage1_projections": stage1_fcfs,
        "stage2_projections": stage2_fcfs,
    }


# ─── Master Function ──────────────────────────────────────────────────────────

def analyze_fundamental(
    ticker: str,
    stock_info: Dict[str, Any],
    raw_financials: Dict[str, Any],
) -> Dict[str, Any]:
    """Combine all fundamental analysis components."""

    raw_income = raw_financials.get("income_statement", [])
    raw_balance = raw_financials.get("balance_sheet", [])
    raw_cashflow = raw_financials.get("cashflow", [])

    income_stmts = parse_income_statements(raw_income)
    balance_sheets = parse_balance_sheets(raw_balance)
    cash_flows = parse_cash_flows(raw_cashflow)
    ratios = compute_ratios(income_stmts, balance_sheets, cash_flows)

    # DCF inputs
    dcf_result = None
    fcf = None
    if cash_flows:
        fcf = cash_flows[0].get("free_cash_flow")
    if not fcf and stock_info.get("free_cashflow"):
        fcf = float(stock_info["free_cashflow"])

    shares = stock_info.get("shares_outstanding")
    current_price = stock_info.get("price")
    beta = stock_info.get("beta") or 1.0
    rf = 0.0525
    market_premium = 0.055
    cost_of_equity = rf + beta * market_premium

    equity_val = stock_info.get("market_cap")
    debt_val = (balance_sheets[0].get("total_debt") if balance_sheets else None)
    cash_val = (balance_sheets[0].get("cash") if balance_sheets else None)
    net_debt = (debt_val - cash_val) if debt_val and cash_val else (debt_val or 0)

    wacc = estimate_wacc(equity_val, debt_val, cost_of_equity)

    # Estimate growth rates from historical data or use analyst estimates
    revenue_cagr = ratios.get("revenue_cagr_3y") or stock_info.get("revenue_growth") or 0.10
    terminal_growth = 0.025

    if fcf and shares and current_price:
        try:
            dcf_result = dcf_valuation(
                fcf=fcf,
                shares_outstanding=shares,
                current_price=current_price,
                growth_1_5=min(max(revenue_cagr, 0.02), 0.35),
                growth_6_10=min(max(revenue_cagr * 0.6, 0.02), 0.20),
                terminal_growth=terminal_growth,
                wacc=wacc,
                net_debt=net_debt,
            )
        except Exception as e:
            logger.warning(f"DCF failed for {ticker}: {e}")

    return {
        "ticker": ticker,
        "income_statements": income_stmts,
        "balance_sheets": balance_sheets,
        "cash_flows": cash_flows,
        "ratios": ratios,
        "dcf": dcf_result,
        "wacc": round(wacc, 4),
        "cost_of_equity": round(cost_of_equity, 4),
        **ratios,
    }
