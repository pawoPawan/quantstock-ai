"""
Scoring Engine — generates 0-100 composite scores across 6 dimensions.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

GRADE_MAP = [
    (95, "A+"), (90, "A"), (85, "A-"),
    (80, "B+"), (75, "B"), (70, "B-"),
    (65, "C+"), (60, "C"), (55, "C-"),
    (50, "D+"), (40, "D"), (0, "F"),
]

RECOMMENDATION_MAP = [
    (85, "Strong Buy"), (70, "Buy"), (55, "Hold"), (40, "Sell"), (0, "Strong Sell"),
]


def _grade(score: float) -> str:
    for threshold, grade in GRADE_MAP:
        if score >= threshold:
            return grade
    return "F"


def _signal(score: float) -> str:
    if score >= 65:
        return "bullish"
    if score <= 35:
        return "bearish"
    return "neutral"


def _recommendation(overall: float) -> str:
    for threshold, rec in RECOMMENDATION_MAP:
        if overall >= threshold:
            return rec
    return "Strong Sell"


def _clamp(val: float, lo: float = 0, hi: float = 100) -> float:
    return max(lo, min(hi, val))


# ─── Dimension Scorers ────────────────────────────────────────────────────────

def score_fundamental(info: Dict[str, Any], fundamental: Dict[str, Any]) -> Dict[str, Any]:
    components = {}
    score = 50.0  # start neutral

    # Valuation relative to growth (PEG)
    peg = info.get("peg_ratio")
    if peg:
        if peg < 1:
            components["peg"] = 20
        elif peg < 2:
            components["peg"] = 12
        elif peg < 3:
            components["peg"] = 5
        else:
            components["peg"] = -5
    else:
        components["peg"] = 0

    # P/E ratio
    pe = info.get("pe_ratio")
    if pe:
        if pe < 15:
            components["pe"] = 15
        elif pe < 25:
            components["pe"] = 10
        elif pe < 40:
            components["pe"] = 2
        else:
            components["pe"] = -8

    # Revenue growth
    rev_growth = info.get("revenue_growth") or fundamental.get("revenue_cagr_3y")
    if rev_growth:
        if rev_growth > 0.25:
            components["growth"] = 20
        elif rev_growth > 0.15:
            components["growth"] = 14
        elif rev_growth > 0.08:
            components["growth"] = 8
        elif rev_growth > 0:
            components["growth"] = 3
        else:
            components["growth"] = -5

    # ROE
    roe = info.get("roe") or fundamental.get("roe")
    if roe:
        if roe > 0.25:
            components["roe"] = 15
        elif roe > 0.15:
            components["roe"] = 10
        elif roe > 0.08:
            components["roe"] = 5
        else:
            components["roe"] = -2

    # Debt management
    de = info.get("debt_to_equity") or fundamental.get("debt_to_equity")
    if de is not None:
        if de < 0.3:
            components["debt"] = 10
        elif de < 0.8:
            components["debt"] = 6
        elif de < 1.5:
            components["debt"] = 2
        else:
            components["debt"] = -8

    # DCF margin of safety
    dcf = fundamental.get("dcf") or {}
    mos = dcf.get("margin_of_safety")
    if mos is not None:
        if mos > 0.3:
            components["dcf"] = 20
        elif mos > 0.1:
            components["dcf"] = 12
        elif mos > -0.1:
            components["dcf"] = 5
        else:
            components["dcf"] = -10

    raw = score + sum(components.values())
    return _build_dimension(raw, components, "Fundamental")


def score_technical(technical: Dict[str, Any]) -> Dict[str, Any]:
    components = {}

    # RSI
    rsi = (technical.get("rsi") or {}).get("value")
    if rsi is not None:
        if rsi < 30:
            components["rsi"] = 15  # oversold
        elif rsi > 70:
            components["rsi"] = -10  # overbought
        elif 40 <= rsi <= 60:
            components["rsi"] = 5   # neutral/healthy
        else:
            components["rsi"] = 2

    # MACD
    macd = technical.get("macd") or {}
    if macd.get("trend") == "bullish":
        components["macd"] = 15
        if macd.get("crossover") == "bullish_cross":
            components["macd"] += 5
    elif macd.get("trend") == "bearish":
        components["macd"] = -10

    # Supertrend
    st = technical.get("supertrend") or {}
    if st.get("signal") == "bullish":
        components["supertrend"] = 15
    elif st.get("signal") == "bearish":
        components["supertrend"] = -12

    # ADX trend strength
    adx = technical.get("adx") or {}
    adx_val = adx.get("value")
    if adx_val:
        if adx_val > 40 and adx.get("signal") == "bullish":
            components["adx"] = 12
        elif adx_val > 25 and adx.get("signal") == "bullish":
            components["adx"] = 8
        elif adx_val > 40 and adx.get("signal") == "bearish":
            components["adx"] = -10
        else:
            components["adx"] = 0

    # Bollinger Band
    bb = technical.get("bollinger_bands") or {}
    pct_b = bb.get("pct_b")
    if pct_b is not None:
        if pct_b < 0.2:
            components["bb"] = 8
        elif pct_b > 0.8:
            components["bb"] = -6
        else:
            components["bb"] = 2

    # Volume / OBV
    obv = technical.get("obv") or {}
    if obv.get("signal") == "bullish":
        components["obv"] = 8
    elif obv.get("signal") == "bearish":
        components["obv"] = -6

    # Ichimoku
    ichi = technical.get("ichimoku") or {}
    if ichi.get("signal") == "bullish":
        components["ichimoku"] = 10
    elif ichi.get("signal") == "bearish":
        components["ichimoku"] = -8

    raw = 50 + sum(components.values())
    return _build_dimension(raw, components, "Technical")


def score_quant(quant: Dict[str, Any]) -> Dict[str, Any]:
    components = {}

    sharpe = quant.get("sharpe_ratio")
    if sharpe is not None:
        if sharpe > 2:
            components["sharpe"] = 20
        elif sharpe > 1:
            components["sharpe"] = 12
        elif sharpe > 0.5:
            components["sharpe"] = 6
        elif sharpe > 0:
            components["sharpe"] = 2
        else:
            components["sharpe"] = -10

    sortino = quant.get("sortino_ratio")
    if sortino is not None:
        if sortino > 2:
            components["sortino"] = 15
        elif sortino > 1:
            components["sortino"] = 8
        elif sortino > 0:
            components["sortino"] = 3
        else:
            components["sortino"] = -8

    mdd = quant.get("max_drawdown")
    if mdd is not None:
        if mdd > -0.10:
            components["drawdown"] = 15
        elif mdd > -0.20:
            components["drawdown"] = 8
        elif mdd > -0.35:
            components["drawdown"] = 2
        else:
            components["drawdown"] = -10

    vol = quant.get("annualized_volatility")
    if vol is not None:
        if vol < 0.15:
            components["volatility"] = 10
        elif vol < 0.30:
            components["volatility"] = 5
        elif vol < 0.50:
            components["volatility"] = 0
        else:
            components["volatility"] = -8

    alpha = quant.get("alpha")
    if alpha is not None:
        if alpha > 0.05:
            components["alpha"] = 15
        elif alpha > 0:
            components["alpha"] = 7
        else:
            components["alpha"] = -5

    raw = 50 + sum(components.values())
    return _build_dimension(raw, components, "Quantitative")


def score_options(options: Dict[str, Any]) -> Dict[str, Any]:
    components = {}

    # IV Rank — high IV = high premium, but also uncertainty
    ivr = options.get("iv_rank")
    if ivr is not None:
        if ivr < 20:
            components["ivr"] = 8   # low IV = stable
        elif ivr < 50:
            components["ivr"] = 5
        elif ivr < 80:
            components["ivr"] = 2
        else:
            components["ivr"] = -5  # very high IV = fear

    # PCR
    pcr = (options.get("put_call_ratio") or {}).get("pcr_oi")
    if pcr is not None:
        if pcr < 0.7:
            components["pcr"] = 12   # calls dominating = bullish
        elif pcr > 1.5:
            components["pcr"] = -12  # puts dominating = bearish/hedge
        else:
            components["pcr"] = 3

    # Gamma squeeze score (high score = risk)
    gss = options.get("gamma_squeeze_score")
    if gss is not None:
        components["gamma_squeeze"] = -gss * 0.2  # penalize high squeeze risk

    # Dealer positioning
    dp = options.get("dealer_positioning")
    if dp == "long_gamma":
        components["dealer_gamma"] = 10  # stabilizing
    elif dp == "short_gamma":
        components["dealer_gamma"] = -8   # destabilizing

    raw = 50 + sum(components.values())
    return _build_dimension(raw, components, "Options")


def score_sentiment(news: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not news:
        return _build_dimension(50, {"news": 0}, "Sentiment")

    components = {}
    ns = news.get("sentiment_score") or 0
    components["news_sentiment"] = ns * 30  # -1 to 1 → -30 to 30

    raw = 50 + sum(components.values())
    return _build_dimension(raw, components, "Sentiment")


def score_risk(info: Dict[str, Any], quant: Dict[str, Any], options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Risk score: higher = LOWER risk. Inverted for display."""
    components = {}

    beta = info.get("beta")
    if beta is not None:
        if 0.5 < beta < 1.2:
            components["beta"] = 15  # healthy beta
        elif beta < 0:
            components["beta"] = 5   # inverse movement
        elif beta > 2:
            components["beta"] = -15
        else:
            components["beta"] = 5

    mdd = quant.get("max_drawdown")
    if mdd is not None:
        if mdd > -0.10:
            components["drawdown_risk"] = 20
        elif mdd > -0.25:
            components["drawdown_risk"] = 10
        elif mdd > -0.40:
            components["drawdown_risk"] = 0
        else:
            components["drawdown_risk"] = -15

    de = info.get("debt_to_equity")
    if de is not None:
        if de < 0.5:
            components["leverage"] = 12
        elif de < 1.5:
            components["leverage"] = 5
        elif de < 3:
            components["leverage"] = -5
        else:
            components["leverage"] = -15

    vol = quant.get("annualized_volatility")
    if vol is not None:
        if vol < 0.20:
            components["vol_risk"] = 15
        elif vol < 0.40:
            components["vol_risk"] = 8
        else:
            components["vol_risk"] = -5

    raw = 50 + sum(components.values())
    return _build_dimension(raw, components, "Risk")


def _build_dimension(raw: float, components: Dict[str, float], label: str) -> Dict[str, Any]:
    score = _clamp(raw)
    return {
        "score": round(score, 2),
        "grade": _grade(score),
        "signal": _signal(score),
        "components": {k: round(v, 2) for k, v in components.items()},
        "explanation": f"{label} score based on {len(components)} factors",
    }


# ─── Composite Score ──────────────────────────────────────────────────────────

WEIGHTS = {
    "fundamental": 0.30,
    "technical": 0.20,
    "quant": 0.20,
    "options": 0.10,
    "sentiment": 0.10,
    "risk": 0.10,
}


def compute_composite_score(
    ticker: str,
    stock_info: Dict[str, Any],
    technical: Dict[str, Any],
    fundamental: Dict[str, Any],
    quant: Dict[str, Any],
    options: Optional[Dict[str, Any]] = None,
    news: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Compute the 0-100 composite QuantScore."""
    fund_score = score_fundamental(stock_info, fundamental)
    tech_score = score_technical(technical)
    quant_score = score_quant(quant)
    opt_score = score_options(options or {})
    sent_score = score_sentiment(news)
    risk_score = score_risk(stock_info, quant, options)

    overall = (
        fund_score["score"] * WEIGHTS["fundamental"]
        + tech_score["score"] * WEIGHTS["technical"]
        + quant_score["score"] * WEIGHTS["quant"]
        + opt_score["score"] * WEIGHTS["options"]
        + sent_score["score"] * WEIGHTS["sentiment"]
        + risk_score["score"] * WEIGHTS["risk"]
    )

    return {
        "ticker": ticker,
        "overall_score": round(overall, 2),
        "overall_grade": _grade(overall),
        "overall_signal": _signal(overall),
        "recommendation": _recommendation(overall),
        "fundamental_score": fund_score,
        "technical_score": tech_score,
        "quant_score": quant_score,
        "options_score": opt_score,
        "sentiment_score": sent_score,
        "risk_score": risk_score,
        "weights": WEIGHTS,
    }
