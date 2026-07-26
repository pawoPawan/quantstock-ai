"""Market data service — fetches price, quote, and fundamental data via yfinance."""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

import numpy as np
import pandas as pd
import yfinance as yf

from app.config import get_settings
from app.core.cache import cache_get, cache_set

logger = logging.getLogger(__name__)
settings = get_settings()

# Map friendly period/interval labels to yfinance params
PERIOD_MAP = {
    "1D": ("1d", "5m"),
    "5D": ("5d", "15m"),
    "1M": ("1mo", "1h"),
    "3M": ("3mo", "1d"),
    "6M": ("6mo", "1d"),
    "1Y": ("1y", "1d"),
    "5Y": ("5y", "1wk"),
    "MAX": ("max", "1mo"),
}


async def get_stock_info(ticker: str) -> Optional[Dict[str, Any]]:
    """Fetch comprehensive stock information including fundamentals."""
    cache_key = f"stock_info:{ticker.upper()}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        t = yf.Ticker(ticker.upper())
        info = t.info

        if not info or "regularMarketPrice" not in info and "currentPrice" not in info:
            return None

        price = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose", 0)
        prev_close = info.get("previousClose", price)
        change = price - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0

        data = {
            "ticker": ticker.upper(),
            "name": info.get("longName") or info.get("shortName", ticker.upper()),
            "price": float(price),
            "change": float(change),
            "change_pct": float(change_pct),
            "volume": int(info.get("regularMarketVolume") or info.get("volume", 0)),
            "avg_volume": info.get("averageDailyVolume3Month") or info.get("averageVolume"),
            "market_cap": info.get("marketCap"),
            "enterprise_value": info.get("enterpriseValue"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "peg_ratio": info.get("pegRatio"),
            "price_to_book": info.get("priceToBook"),
            "price_to_sales": info.get("priceToSalesTrailing12Months"),
            "eps": info.get("trailingEps"),
            "eps_forward": info.get("forwardEps"),
            "dividend_yield": info.get("dividendYield"),
            "dividend_rate": info.get("dividendRate"),
            "week_52_high": info.get("fiftyTwoWeekHigh"),
            "week_52_low": info.get("fiftyTwoWeekLow"),
            "beta": info.get("beta"),
            "roe": info.get("returnOnEquity"),
            "roa": info.get("returnOnAssets"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "operating_margin": info.get("operatingMargins"),
            "profit_margin": info.get("profitMargins"),
            "gross_margins": info.get("grossMargins"),
            "ebitda_margins": info.get("ebitdaMargins"),
            "debt_to_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            "quick_ratio": info.get("quickRatio"),
            "free_cashflow": info.get("freeCashflow"),
            "operating_cashflow": info.get("operatingCashflow"),
            "total_revenue": info.get("totalRevenue"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "country": info.get("country"),
            "website": info.get("website"),
            "description": info.get("longBusinessSummary"),
            "employees": info.get("fullTimeEmployees"),
            "exchange": info.get("exchange"),
            "currency": info.get("currency", "USD"),
            "shares_outstanding": info.get("sharesOutstanding"),
            "float_shares": info.get("floatShares"),
            "insider_ownership": info.get("heldPercentInsiders"),
            "institutional_ownership": info.get("heldPercentInstitutions"),
            "short_ratio": info.get("shortRatio"),
            "short_percent": info.get("shortPercentOfFloat"),
            "timestamp": datetime.utcnow().isoformat(),
        }

        await cache_set(cache_key, data, settings.cache_ttl_market_data)
        return data

    except Exception as e:
        logger.error(f"Error fetching stock info for {ticker}: {e}")
        return None


async def get_historical_prices(
    ticker: str,
    period: str = "1Y",
    interval: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Fetch OHLCV historical price data."""
    yf_period, default_interval = PERIOD_MAP.get(period.upper(), ("1y", "1d"))
    yf_interval = interval or default_interval

    cache_key = f"history:{ticker.upper()}:{period}:{yf_interval}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        t = yf.Ticker(ticker.upper())
        df = t.history(period=yf_period, interval=yf_interval, auto_adjust=True)

        if df.empty:
            return None

        df.index = pd.to_datetime(df.index)
        df = df.dropna()

        bars = []
        for ts, row in df.iterrows():
            bars.append({
                "timestamp": ts.isoformat(),
                "open": round(float(row["Open"]), 4),
                "high": round(float(row["High"]), 4),
                "low": round(float(row["Low"]), 4),
                "close": round(float(row["Close"]), 4),
                "volume": int(row["Volume"]),
            })

        data = {
            "ticker": ticker.upper(),
            "period": period,
            "interval": yf_interval,
            "bars": bars,
        }

        ttl = 60 if yf_interval in ("1m", "5m", "15m") else settings.cache_ttl_technical
        await cache_set(cache_key, data, ttl)
        return data

    except Exception as e:
        logger.error(f"Error fetching historical data for {ticker}: {e}")
        return None


async def get_financial_statements(ticker: str) -> Optional[Dict[str, Any]]:
    """Fetch income statement, balance sheet, and cash flow statements."""
    cache_key = f"financials:{ticker.upper()}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        t = yf.Ticker(ticker.upper())

        income = _parse_financials(t.financials)
        quarterly_income = _parse_financials(t.quarterly_financials)
        balance = _parse_financials(t.balance_sheet)
        cashflow = _parse_financials(t.cashflow)

        data = {
            "ticker": ticker.upper(),
            "income_statement": income,
            "quarterly_income": quarterly_income,
            "balance_sheet": balance,
            "cashflow": cashflow,
        }

        await cache_set(cache_key, data, settings.cache_ttl_fundamental)
        return data

    except Exception as e:
        logger.error(f"Error fetching financials for {ticker}: {e}")
        return None


def _parse_financials(df: pd.DataFrame) -> List[Dict[str, Any]]:
    if df is None or df.empty:
        return []
    result = []
    for col in df.columns:
        row = {"date": str(col)[:10]}
        for idx in df.index:
            val = df.loc[idx, col]
            if pd.notna(val):
                row[_clean_key(str(idx))] = float(val)
        result.append(row)
    return result


def _clean_key(key: str) -> str:
    return key.lower().replace(" ", "_").replace("/", "_").replace("-", "_")


async def get_options_chain(ticker: str, expiry: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetch options chain data for a given ticker."""
    cache_key = f"options:{ticker.upper()}:{expiry or 'all'}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        t = yf.Ticker(ticker.upper())
        expiry_dates = list(t.options) if t.options else []

        if not expiry_dates:
            return None

        target_expiry = expiry if expiry and expiry in expiry_dates else expiry_dates[0]
        opt = t.option_chain(target_expiry)

        calls_df = opt.calls.copy()
        puts_df = opt.puts.copy()

        # Align on strike
        all_strikes = sorted(
            set(calls_df["strike"].tolist()) | set(puts_df["strike"].tolist())
        )

        chain = []
        days_to_expiry = _days_to_expiry(target_expiry)

        for strike in all_strikes:
            call_row = calls_df[calls_df["strike"] == strike]
            put_row = puts_df[puts_df["strike"] == strike]

            entry = {
                "strike": strike,
                "expiry": target_expiry,
                "days_to_expiry": days_to_expiry,
            }

            if not call_row.empty:
                c = call_row.iloc[0]
                entry.update({
                    "call_price": _safe_float(c.get("lastPrice")),
                    "call_bid": _safe_float(c.get("bid")),
                    "call_ask": _safe_float(c.get("ask")),
                    "call_iv": _safe_float(c.get("impliedVolatility")),
                    "call_delta": _safe_float(c.get("delta")),
                    "call_oi": _safe_int(c.get("openInterest")),
                    "call_oi_change": _safe_int(c.get("openInterestChange")),
                    "call_volume": _safe_int(c.get("volume")),
                    "in_the_money_call": bool(c.get("inTheMoney", False)),
                })

            if not put_row.empty:
                p = put_row.iloc[0]
                entry.update({
                    "put_price": _safe_float(p.get("lastPrice")),
                    "put_bid": _safe_float(p.get("bid")),
                    "put_ask": _safe_float(p.get("ask")),
                    "put_iv": _safe_float(p.get("impliedVolatility")),
                    "put_delta": _safe_float(p.get("delta")),
                    "put_oi": _safe_int(p.get("openInterest")),
                    "put_oi_change": _safe_int(p.get("openInterestChange")),
                    "put_volume": _safe_int(p.get("volume")),
                    "in_the_money_put": bool(p.get("inTheMoney", False)),
                })

            chain.append(entry)

        data = {
            "ticker": ticker.upper(),
            "expiry_dates": expiry_dates,
            "selected_expiry": target_expiry,
            "days_to_expiry": days_to_expiry,
            "chain": chain,
        }

        await cache_set(cache_key, data, settings.cache_ttl_options)
        return data

    except Exception as e:
        logger.error(f"Error fetching options chain for {ticker}: {e}")
        return None


def _days_to_expiry(expiry_str: str) -> int:
    try:
        expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d")
        return max(0, (expiry_date - datetime.utcnow()).days)
    except Exception:
        return 30


def _safe_float(val) -> Optional[float]:
    try:
        v = float(val)
        return round(v, 6) if not np.isnan(v) else None
    except Exception:
        return None


def _safe_int(val) -> Optional[int]:
    try:
        v = int(val)
        return v if v >= 0 else None
    except Exception:
        return None


async def search_stocks(query: str) -> List[Dict[str, Any]]:
    """Search for stocks by ticker or company name."""
    try:
        results = yf.Search(query, max_results=10)
        quotes = results.quotes if hasattr(results, "quotes") else []
        return [
            {
                "ticker": q.get("symbol", ""),
                "name": q.get("longname") or q.get("shortname", ""),
                "exchange": q.get("exchange", ""),
                "type": q.get("quoteType", ""),
            }
            for q in quotes
            if q.get("symbol")
        ]
    except Exception as e:
        logger.error(f"Search error: {e}")
        return []
