"""Stock analysis router — aggregates all analysis modules."""

import logging
from typing import Optional
import pandas as pd
import yfinance as yf

from fastapi import APIRouter, HTTPException, Query

from app.config import get_settings
from app.core.cache import cache_get, cache_set
from app.services import market_data, technical_analysis, fundamental_analysis, quant_analysis, options_analysis, scoring_engine, ai_insights

router = APIRouter(prefix="/stocks", tags=["stocks"])
logger = logging.getLogger(__name__)
settings = get_settings()


@router.get("/search")
async def search_stocks(q: str = Query(..., min_length=1)):
    results = await market_data.search_stocks(q)
    return {"results": results}


@router.get("/{ticker}/info")
async def get_stock_info(ticker: str):
    info = await market_data.get_stock_info(ticker)
    if not info:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found")
    return info


@router.get("/{ticker}/history")
async def get_history(
    ticker: str,
    period: str = Query("1Y", description="1D, 5D, 1M, 3M, 6M, 1Y, 5Y, MAX"),
    interval: Optional[str] = None,
):
    data = await market_data.get_historical_prices(ticker, period, interval)
    if not data:
        raise HTTPException(status_code=404, detail="No historical data found")
    return data


@router.get("/{ticker}/technical")
async def get_technical(ticker: str, period: str = Query("1Y")):
    cache_key = f"technical:{ticker.upper()}:{period}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    hist = await market_data.get_historical_prices(ticker, period)
    if not hist or not hist.get("bars"):
        raise HTTPException(status_code=404, detail="No data for technical analysis")

    bars = hist["bars"]
    df = pd.DataFrame(bars)
    df.index = pd.to_datetime(df["timestamp"])
    df = df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})

    result = technical_analysis.analyze_technical(df)
    result["ticker"] = ticker.upper()
    await cache_set(cache_key, result, settings.cache_ttl_technical)
    return result


@router.get("/{ticker}/fundamental")
async def get_fundamental(ticker: str):
    cache_key = f"fundamental:{ticker.upper()}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    info = await market_data.get_stock_info(ticker)
    if not info:
        raise HTTPException(status_code=404, detail="Ticker not found")

    raw_fin = await market_data.get_financial_statements(ticker)
    if not raw_fin:
        raise HTTPException(status_code=404, detail="Financial statements not available")

    result = fundamental_analysis.analyze_fundamental(ticker, info, raw_fin)
    await cache_set(cache_key, result, settings.cache_ttl_fundamental)
    return result


@router.get("/{ticker}/quant")
async def get_quant(ticker: str, period: str = Query("2Y")):
    cache_key = f"quant:{ticker.upper()}:{period}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    hist = await market_data.get_historical_prices(ticker, period)
    market_hist = await market_data.get_historical_prices("SPY", period)

    if not hist or not hist.get("bars"):
        raise HTTPException(status_code=404, detail="No price history")

    prices = [b["close"] for b in hist["bars"]]
    mkt_prices = [b["close"] for b in market_hist["bars"]] if market_hist else None

    result = quant_analysis.analyze_quant(ticker, prices, mkt_prices, settings.risk_free_rate)
    await cache_set(cache_key, result, settings.cache_ttl_technical)
    return result


@router.get("/{ticker}/options")
async def get_options(ticker: str, expiry: Optional[str] = None):
    cache_key = f"options_analysis:{ticker.upper()}:{expiry or 'nearest'}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    info = await market_data.get_stock_info(ticker)
    if not info:
        raise HTTPException(status_code=404, detail="Ticker not found")

    spot = info["price"]
    chain_data = await market_data.get_options_chain(ticker, expiry)
    if not chain_data:
        raise HTTPException(status_code=404, detail="Options data not available")

    hist = await market_data.get_historical_prices(ticker, "1Y")
    close_prices = [b["close"] for b in hist["bars"]] if hist else [spot]

    result = options_analysis.analyze_options(
        ticker=ticker,
        spot=spot,
        chain=chain_data.get("chain", []),
        close_prices=close_prices,
        expiry_dates=chain_data.get("expiry_dates", []),
        selected_expiry=chain_data.get("selected_expiry", ""),
    )
    await cache_set(cache_key, result, settings.cache_ttl_options)
    return result


@router.get("/{ticker}/score")
async def get_score(ticker: str):
    """Compute composite QuantScore across all dimensions."""
    cache_key = f"score:{ticker.upper()}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    info = await market_data.get_stock_info(ticker)
    if not info:
        raise HTTPException(status_code=404, detail="Ticker not found")

    hist = await market_data.get_historical_prices(ticker, "2Y")
    mkt_hist = await market_data.get_historical_prices("SPY", "2Y")
    raw_fin = await market_data.get_financial_statements(ticker)
    chain_data = await market_data.get_options_chain(ticker)

    prices = [b["close"] for b in hist["bars"]] if hist else [info["price"]]
    mkt_prices = [b["close"] for b in mkt_hist["bars"]] if mkt_hist else None

    bars = (hist.get("bars") or [])
    df = pd.DataFrame(bars) if bars else pd.DataFrame()
    if not df.empty:
        df.index = pd.to_datetime(df["timestamp"])
        df = df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})

    tech = technical_analysis.analyze_technical(df) if not df.empty else {}
    fund = fundamental_analysis.analyze_fundamental(ticker, info, raw_fin or {}) if raw_fin else {}
    quant = quant_analysis.analyze_quant(ticker, prices, mkt_prices, settings.risk_free_rate)

    opt_result = None
    if chain_data:
        close_prices = [b["close"] for b in bars] if bars else [info["price"]]
        opt_result = options_analysis.analyze_options(
            ticker, info["price"],
            chain_data.get("chain", []),
            close_prices,
            chain_data.get("expiry_dates", []),
            chain_data.get("selected_expiry", ""),
        )

    score = scoring_engine.compute_composite_score(
        ticker=ticker,
        stock_info=info,
        technical=tech,
        fundamental=fund,
        quant=quant,
        options=opt_result,
        news=None,
    )
    await cache_set(cache_key, score, 300)
    return score


@router.get("/{ticker}/insights")
async def get_ai_insights(ticker: str):
    """Generate AI-powered insights for the ticker."""
    cache_key = f"insights:{ticker.upper()}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    info = await market_data.get_stock_info(ticker)
    if not info:
        raise HTTPException(status_code=404, detail="Ticker not found")

    hist = await market_data.get_historical_prices(ticker, "2Y")
    mkt_hist = await market_data.get_historical_prices("SPY", "2Y")
    raw_fin = await market_data.get_financial_statements(ticker)
    chain_data = await market_data.get_options_chain(ticker)

    prices = [b["close"] for b in hist["bars"]] if hist else [info["price"]]
    mkt_prices = [b["close"] for b in mkt_hist["bars"]] if mkt_hist else None

    bars = (hist.get("bars") or [])
    df = pd.DataFrame(bars) if bars else pd.DataFrame()
    if not df.empty:
        df.index = pd.to_datetime(df["timestamp"])
        df = df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})

    tech = technical_analysis.analyze_technical(df) if not df.empty else {}
    fund = fundamental_analysis.analyze_fundamental(ticker, info, raw_fin or {}) if raw_fin else {}
    quant_data = quant_analysis.analyze_quant(ticker, prices, mkt_prices, settings.risk_free_rate)

    opt_result = None
    if chain_data:
        opt_result = options_analysis.analyze_options(
            ticker, info["price"],
            chain_data.get("chain", []),
            prices,
            chain_data.get("expiry_dates", []),
            chain_data.get("selected_expiry", ""),
        )

    score = scoring_engine.compute_composite_score(ticker, info, tech, fund, quant_data, opt_result)
    insights = ai_insights.generate_insights(ticker, info, tech, fund, quant_data, opt_result, score)

    await cache_set(cache_key, insights, settings.cache_ttl_news)
    return insights


@router.get("/{ticker}/full")
async def get_full_analysis(ticker: str):
    """Single endpoint for complete analysis — used by the dashboard."""
    cache_key = f"full:{ticker.upper()}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    info = await market_data.get_stock_info(ticker)
    if not info:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found")

    hist = await market_data.get_historical_prices(ticker, "2Y")
    mkt_hist = await market_data.get_historical_prices("SPY", "2Y")
    raw_fin = await market_data.get_financial_statements(ticker)
    chain_data = await market_data.get_options_chain(ticker)

    bars = (hist.get("bars") or []) if hist else []
    prices = [b["close"] for b in bars]
    mkt_prices = [b["close"] for b in mkt_hist["bars"]] if mkt_hist else None

    df = pd.DataFrame(bars) if bars else pd.DataFrame()
    if not df.empty:
        df.index = pd.to_datetime(df["timestamp"])
        df = df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})

    tech = technical_analysis.analyze_technical(df) if not df.empty else {}
    fund = fundamental_analysis.analyze_fundamental(ticker, info, raw_fin or {}) if raw_fin else {}
    quant_data = quant_analysis.analyze_quant(ticker, prices or [info["price"]], mkt_prices, settings.risk_free_rate)

    opt_result = None
    if chain_data:
        opt_result = options_analysis.analyze_options(
            ticker, info["price"],
            chain_data.get("chain", []),
            prices or [info["price"]],
            chain_data.get("expiry_dates", []),
            chain_data.get("selected_expiry", ""),
        )

    score = scoring_engine.compute_composite_score(ticker, info, tech, fund, quant_data, opt_result)
    insights = ai_insights.generate_insights(ticker, info, tech, fund, quant_data, opt_result, score)

    result = {
        "ticker": ticker.upper(),
        "stock_info": info,
        "technical": tech,
        "fundamental": fund,
        "quant": quant_data,
        "options": opt_result,
        "score": score,
        "insights": insights,
        "price_history": hist,
    }

    await cache_set(cache_key, result, settings.cache_ttl_market_data)
    return result


@router.post("/{ticker}/bs")
async def black_scholes_calculator(
    ticker: str,
    stock_price: float = Query(...),
    strike: float = Query(...),
    time_to_expiry: float = Query(..., description="Years"),
    risk_free_rate: float = Query(0.0525),
    volatility: float = Query(...),
):
    from app.services.options_analysis import full_bs_analysis
    try:
        result = full_bs_analysis(stock_price, strike, time_to_expiry, risk_free_rate, volatility)
        return result
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
