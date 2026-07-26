"""Portfolio analysis router."""

import logging
from typing import List, Dict, Any
import numpy as np

from fastapi import APIRouter, HTTPException

from app.services.market_data import get_stock_info, get_historical_prices
from app.services.quant_analysis import compute_returns, annualized_return, annualized_volatility, sharpe_ratio

router = APIRouter(prefix="/portfolio", tags=["portfolio"])
logger = logging.getLogger(__name__)


@router.post("/analyze")
async def analyze_portfolio(positions: List[Dict[str, Any]]):
    """
    positions: [{ticker, shares, avg_cost}, ...]
    Returns portfolio-level analytics including correlation matrix, Sharpe, volatility.
    """
    if not positions:
        raise HTTPException(status_code=400, detail="No positions provided")

    enriched = []
    price_matrix = {}
    total_cost = 0.0
    total_value = 0.0

    for pos in positions:
        ticker = pos.get("ticker", "").upper()
        shares = float(pos.get("shares", 0))
        avg_cost = float(pos.get("avg_cost", 0))

        info = await get_stock_info(ticker)
        hist = await get_historical_prices(ticker, "1Y")

        current_price = info["price"] if info else avg_cost
        market_value = current_price * shares
        cost_basis = avg_cost * shares
        pnl = market_value - cost_basis
        pnl_pct = pnl / cost_basis if cost_basis else 0

        enriched.append({
            "ticker": ticker,
            "shares": shares,
            "avg_cost": avg_cost,
            "current_price": current_price,
            "market_value": round(market_value, 2),
            "cost_basis": round(cost_basis, 2),
            "unrealized_pnl": round(pnl, 2),
            "unrealized_pnl_pct": round(pnl_pct * 100, 2),
            "name": info.get("name", ticker) if info else ticker,
            "sector": info.get("sector") if info else None,
        })

        total_cost += cost_basis
        total_value += market_value

        if hist:
            price_matrix[ticker] = [b["close"] for b in hist["bars"]]

    # Add weight
    for pos in enriched:
        pos["weight"] = round(pos["market_value"] / total_value * 100, 2) if total_value else 0

    # Portfolio-level metrics
    analytics = _portfolio_analytics(price_matrix, enriched, total_value)

    return {
        "positions": enriched,
        "total_value": round(total_value, 2),
        "total_cost": round(total_cost, 2),
        "total_pnl": round(total_value - total_cost, 2),
        "total_pnl_pct": round((total_value - total_cost) / total_cost * 100, 2) if total_cost else 0,
        **analytics,
    }


def _portfolio_analytics(price_matrix: Dict[str, List[float]], positions: List[Dict], total_value: float) -> Dict[str, Any]:
    if not price_matrix or total_value == 0:
        return {}

    weights = {}
    for pos in positions:
        weights[pos["ticker"]] = pos.get("weight", 0) / 100

    # Align lengths
    min_len = min(len(p) for p in price_matrix.values())
    returns_matrix = {}
    for ticker, prices in price_matrix.items():
        prices_aligned = prices[-min_len:]
        r = compute_returns(prices_aligned)
        if len(r) > 1:
            returns_matrix[ticker] = r

    if not returns_matrix:
        return {}

    tickers = list(returns_matrix.keys())
    min_ret_len = min(len(r) for r in returns_matrix.values())
    ret_array = np.array([returns_matrix[t][-min_ret_len:] for t in tickers])  # shape: (n_assets, n_days)

    w = np.array([weights.get(t, 0) for t in tickers])
    w = w / w.sum() if w.sum() > 0 else np.ones(len(tickers)) / len(tickers)

    port_returns = ret_array.T @ w
    port_sharpe = sharpe_ratio(port_returns)
    port_vol = annualized_volatility(port_returns)
    port_ret = annualized_return(port_returns)

    # Correlation matrix
    corr = np.corrcoef(ret_array)
    corr_matrix = {
        tickers[i]: {tickers[j]: round(float(corr[i, j]), 4) for j in range(len(tickers))}
        for i in range(len(tickers))
    }

    # Diversification score (1 - avg off-diagonal correlation)
    n = len(tickers)
    if n > 1:
        off_diag = [abs(corr[i, j]) for i in range(n) for j in range(n) if i != j]
        avg_corr = np.mean(off_diag)
        div_score = round((1 - avg_corr) * 100, 1)
    else:
        div_score = 0

    # Efficient frontier (simplified Monte Carlo)
    ef_points = _efficient_frontier(ret_array, n_points=30) if n >= 2 else []

    return {
        "portfolio_return": round(port_ret * 100, 2),
        "portfolio_volatility": round(port_vol * 100, 2),
        "portfolio_sharpe": round(port_sharpe, 4),
        "diversification_score": div_score,
        "correlation_matrix": corr_matrix,
        "efficient_frontier": ef_points,
    }


def _efficient_frontier(ret_array: np.ndarray, n_points: int = 30) -> List[Dict[str, float]]:
    """Monte Carlo efficient frontier via random weight sampling."""
    n_assets = ret_array.shape[0]
    min_ret_len = ret_array.shape[1]
    points = []
    for _ in range(500):
        w = np.random.dirichlet(np.ones(n_assets))
        port_r = ret_array.T @ w
        ret = annualized_return(port_r) * 100
        vol = annualized_volatility(port_r) * 100
        sr = (annualized_return(port_r) - 0.05) / (annualized_volatility(port_r) + 1e-8)
        points.append({"return": round(ret, 2), "volatility": round(vol, 2), "sharpe": round(sr, 4)})
    # Return Pareto-efficient frontier subset
    points.sort(key=lambda x: x["volatility"])
    return points[:n_points]
