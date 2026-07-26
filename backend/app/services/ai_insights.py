"""
AI Insights service — generates qualitative analysis from quantitative data.
Produces structured insights without requiring an external LLM (rule-based),
but can be extended with an OpenAI call when OPENAI_API_KEY is set.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def generate_insights(
    ticker: str,
    stock_info: Dict[str, Any],
    technical: Dict[str, Any],
    fundamental: Dict[str, Any],
    quant: Dict[str, Any],
    options: Optional[Dict[str, Any]],
    score: Dict[str, Any],
) -> Dict[str, Any]:
    """Rule-based AI insights generator."""

    name = stock_info.get("name", ticker)
    price = stock_info.get("price", 0)
    sector = stock_info.get("sector", "Unknown")
    rec = score.get("recommendation", "Hold")
    overall = score.get("overall_score", 50)

    pros = _build_pros(stock_info, fundamental, technical, quant, score)
    cons = _build_cons(stock_info, fundamental, technical, quant)
    risks = _build_risks(stock_info, fundamental, quant, options)
    growth_drivers = _build_growth_drivers(stock_info, fundamental)
    valuation = _valuation_commentary(stock_info, fundamental)
    tech_trend = _technical_trend(technical)
    inst_positioning = _institutional_positioning(stock_info, options)
    options_pos = _options_positioning(options) if options else "Options data unavailable"
    summary = _build_summary(name, ticker, rec, overall, pros, cons, valuation)

    return {
        "ticker": ticker,
        "rating": rec,
        "rating_score": round(overall, 1),
        "pros": pros[:6],
        "cons": cons[:5],
        "risks": risks[:5],
        "growth_drivers": growth_drivers[:5],
        "valuation_commentary": valuation,
        "technical_trend": tech_trend,
        "institutional_positioning": inst_positioning,
        "options_positioning": options_pos,
        "summary": summary,
        "sector": sector,
        "timestamp": datetime.utcnow().isoformat(),
    }


def _build_pros(info, fundamental, technical, quant, score) -> List[str]:
    pros = []

    rev_growth = info.get("revenue_growth") or fundamental.get("revenue_cagr_3y")
    if rev_growth and rev_growth > 0.15:
        pros.append(f"Strong revenue growth of {rev_growth*100:.1f}% demonstrates robust business momentum")

    roe = info.get("roe") or fundamental.get("roe")
    if roe and roe > 0.20:
        pros.append(f"Exceptional ROE of {roe*100:.1f}% indicates efficient capital deployment")

    op_margin = info.get("operating_margin") or fundamental.get("operating_margin")
    if op_margin and op_margin > 0.20:
        pros.append(f"High operating margins of {op_margin*100:.1f}% reflect pricing power and operational efficiency")

    de = info.get("debt_to_equity") or fundamental.get("debt_to_equity")
    if de is not None and de < 0.5:
        pros.append(f"Conservative balance sheet with debt/equity of {de:.2f} provides financial flexibility")

    dcf = (fundamental.get("dcf") or {})
    mos = dcf.get("margin_of_safety")
    if mos and mos > 0.15:
        pros.append(f"DCF analysis suggests {mos*100:.0f}% margin of safety at current prices")

    sharpe = quant.get("sharpe_ratio")
    if sharpe and sharpe > 1.5:
        pros.append(f"Strong Sharpe ratio of {sharpe:.2f} reflects superior risk-adjusted returns")

    tech_signal = technical.get("overall_signal", "")
    if "bullish" in tech_signal:
        pros.append("Technical momentum is bullish with multiple indicators confirming uptrend")

    st = (technical.get("supertrend") or {})
    if st.get("signal") == "bullish":
        pros.append("SuperTrend indicator confirms price is trading above trend line")

    beta = info.get("beta")
    if beta and beta < 0.8:
        pros.append(f"Low beta of {beta:.2f} provides defensive characteristics in volatile markets")

    fcf = info.get("free_cashflow")
    if fcf and fcf > 0:
        pros.append(f"Positive free cash flow of ${fcf/1e9:.2f}B supports dividends and buybacks")

    dividend_yield = info.get("dividend_yield")
    if dividend_yield and dividend_yield > 0.02:
        pros.append(f"Attractive dividend yield of {dividend_yield*100:.1f}% provides income stream")

    return pros[:8] if pros else ["Limited positive catalysts identified at current levels"]


def _build_cons(info, fundamental, technical, quant) -> List[str]:
    cons = []

    pe = info.get("pe_ratio")
    if pe and pe > 35:
        cons.append(f"Elevated P/E ratio of {pe:.1f}x prices in significant growth — execution risk is high")

    de = info.get("debt_to_equity") or fundamental.get("debt_to_equity")
    if de and de > 1.5:
        cons.append(f"High leverage with debt/equity of {de:.2f} amplifies downside in economic slowdowns")

    mdd = quant.get("max_drawdown")
    if mdd and mdd < -0.30:
        cons.append(f"Historical max drawdown of {mdd*100:.1f}% indicates significant drawdown risk")

    rsi = (technical.get("rsi") or {}).get("value")
    if rsi and rsi > 70:
        cons.append(f"RSI of {rsi:.1f} is in overbought territory — near-term pullback is possible")

    vol = quant.get("annualized_volatility")
    if vol and vol > 0.40:
        cons.append(f"High annualized volatility of {vol*100:.1f}% makes position sizing challenging")

    rev_growth = info.get("revenue_growth")
    if rev_growth is not None and rev_growth < 0:
        cons.append(f"Declining revenue growth of {rev_growth*100:.1f}% signals potential business headwinds")

    profit_margin = info.get("profit_margin")
    if profit_margin is not None and profit_margin < 0.05:
        cons.append("Thin profit margins leave little room for error in execution")

    return cons[:6] if cons else ["Moderate risk profile — no significant negatives identified"]


def _build_risks(info, fundamental, quant, options) -> List[str]:
    risks = [
        "Macroeconomic headwinds including rising interest rates and global recession risk",
        "Competitive pressure in the sector could compress margins over time",
        "Regulatory changes may impact business model and profitability",
    ]

    beta = info.get("beta")
    if beta and beta > 1.5:
        risks.append(f"High beta ({beta:.2f}) amplifies market downturns — sharp drawdowns are possible")

    de = info.get("debt_to_equity") or fundamental.get("debt_to_equity")
    if de and de > 2:
        risks.append("Heavy debt burden increases refinancing risk, especially in rising rate environments")

    if options:
        gss = options.get("gamma_squeeze_score")
        if gss and gss > 50:
            risks.append("Elevated gamma exposure creates risk of sharp price dislocation")

    peg = info.get("peg_ratio")
    if peg and peg > 3:
        risks.append("Premium valuation is highly sensitive to earnings disappointments")

    return risks[:6]


def _build_growth_drivers(info, fundamental) -> List[str]:
    drivers = []

    sector = info.get("sector", "")
    industry = info.get("industry", "")

    rev_growth = info.get("revenue_growth") or fundamental.get("revenue_cagr_3y")
    if rev_growth and rev_growth > 0.10:
        drivers.append(f"Accelerating revenue trajectory ({rev_growth*100:.1f}% CAGR) driven by market share gains")

    if "Technology" in sector or "Software" in industry:
        drivers.append("Digital transformation tailwinds support multi-year revenue expansion")
        drivers.append("High switching costs and network effects create durable competitive moat")

    if "Healthcare" in sector:
        drivers.append("Aging demographics and healthcare innovation drive secular demand growth")

    if "Energy" in sector:
        drivers.append("Energy transition and infrastructure investment create long-term opportunities")

    fcf = info.get("free_cashflow")
    if fcf and fcf > 0:
        drivers.append("Strong free cash flow enables capital returns (buybacks/dividends) and M&A")

    employees = info.get("employees")
    if employees and employees > 50000:
        drivers.append("Large workforce enables operational leverage as revenue scales")

    drivers.append("Expanding addressable market and product innovation pipeline")
    drivers.append("International expansion opportunities in emerging markets")

    return drivers[:6]


def _valuation_commentary(info, fundamental) -> str:
    pe = info.get("pe_ratio")
    peg = info.get("peg_ratio")
    pb = info.get("price_to_book")
    dcf = fundamental.get("dcf") or {}
    upside = dcf.get("upside_pct")
    mos = dcf.get("margin_of_safety")

    parts = []
    if pe:
        parts.append(f"trading at {pe:.1f}x trailing earnings")
    if peg:
        grade = "undervalued" if peg < 1 else "fairly valued" if peg < 2 else "premium-priced"
        parts.append(f"PEG of {peg:.2f} suggests the stock is {grade}")
    if upside is not None:
        direction = "upside" if upside > 0 else "downside"
        parts.append(f"DCF model implies {abs(upside):.1f}% {direction} from current levels")
    if mos:
        parts.append(f"margin of safety of {mos*100:.0f}% {'is present' if mos > 0 else 'is absent'}")

    if not parts:
        return "Insufficient data for comprehensive valuation assessment"

    return f"The company is {', '.join(parts)}. " + (
        "The valuation appears attractive for long-term investors." if (peg or 2) < 1.5 else
        "The premium valuation requires strong execution to justify."
    )


def _technical_trend(technical) -> str:
    signal = technical.get("overall_signal", "neutral")
    counts = technical.get("signal_counts", {})
    rsi = (technical.get("rsi") or {}).get("value")
    macd_trend = (technical.get("macd") or {}).get("trend")
    st_signal = (technical.get("supertrend") or {}).get("signal")

    bull = counts.get("bullish", 0)
    bear = counts.get("bearish", 0)

    trend_desc = (
        f"Technical picture is {'strongly' if abs(bull - bear) > 3 else 'moderately'} "
        f"{'bullish' if bull > bear else 'bearish' if bear > bull else 'mixed'} "
        f"with {bull}/{bull+bear+counts.get('neutral',0)} indicators bullish. "
    )

    if rsi:
        if rsi > 70:
            trend_desc += f"RSI at {rsi:.0f} is overbought — watch for reversal. "
        elif rsi < 30:
            trend_desc += f"RSI at {rsi:.0f} is oversold — potential bounce setup. "
        else:
            trend_desc += f"RSI at {rsi:.0f} has room to run in both directions. "

    if st_signal:
        trend_desc += f"SuperTrend confirms {st_signal} momentum. "

    return trend_desc.strip()


def _institutional_positioning(info, options) -> str:
    inst_own = info.get("institutional_ownership")
    insider_own = info.get("insider_ownership")
    short_pct = info.get("short_percent")

    parts = []
    if inst_own:
        parts.append(f"Institutional ownership at {inst_own*100:.1f}%")
        if inst_own > 0.70:
            parts.append("— high institutional conviction stock")
    if insider_own:
        parts.append(f"insider ownership at {insider_own*100:.1f}%")
        if insider_own > 0.10:
            parts.append("indicating strong management confidence")
    if short_pct:
        if short_pct > 0.15:
            parts.append(f"short interest elevated at {short_pct*100:.1f}% of float — squeeze potential if thesis plays out")
        else:
            parts.append(f"short interest modest at {short_pct*100:.1f}% of float")

    return ". ".join(parts) if parts else "Institutional positioning data unavailable"


def _options_positioning(options) -> str:
    if not options:
        return "Options data unavailable"

    pcr = (options.get("put_call_ratio") or {}).get("pcr_oi")
    iv_rank = options.get("iv_rank")
    max_pain = options.get("max_pain")
    spot = options.get("spot_price")
    dealer = options.get("dealer_positioning", "")
    gss = options.get("gamma_squeeze_score", 0)

    parts = []
    if pcr:
        sentiment = "bearish put dominance" if pcr > 1.3 else ("bullish call dominance" if pcr < 0.7 else "neutral")
        parts.append(f"Put/call ratio of {pcr:.2f} shows {sentiment}")

    if iv_rank is not None:
        parts.append(f"IV rank at {iv_rank:.0f}th percentile — {'expensive premium' if iv_rank > 75 else 'cheap premium' if iv_rank < 25 else 'fair premium'}")

    if max_pain and spot:
        diff_pct = (spot - max_pain) / spot * 100
        parts.append(f"Max pain at ${max_pain:.2f} ({diff_pct:+.1f}% from spot) — price tends to gravitate here at expiry")

    if dealer:
        parts.append(f"Dealers are {dealer.replace('_', ' ')} — {'stabilizing price action' if 'long' in dealer else 'amplifying moves'}")

    if gss > 40:
        parts.append(f"Gamma squeeze score of {gss:.0f}/100 indicates elevated squeeze risk")

    return ". ".join(parts) if parts else "Limited options flow data available"


def _build_summary(name, ticker, rec, overall, pros, cons, valuation) -> str:
    sentiment = "compelling" if overall >= 75 else ("attractive" if overall >= 65 else ("mixed" if overall >= 50 else "cautious"))
    return (
        f"{name} ({ticker}) presents a {sentiment} investment case with an overall QuantScore of {overall:.0f}/100, "
        f"warranting a {rec} recommendation. "
        f"{valuation} "
        f"Key positives include {pros[0].lower() if pros else 'stable fundamentals'}. "
        f"{'Primary concern: ' + cons[0].lower() + '. ' if cons else ''}"
        f"Investors should weigh these factors alongside their own risk tolerance and investment horizon."
    )
