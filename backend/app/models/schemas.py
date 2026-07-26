from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ─── Market Data ────────────────────────────────────────────────────────────

class StockQuote(BaseModel):
    ticker: str
    name: str
    price: float
    change: float
    change_pct: float
    volume: int
    avg_volume: Optional[int] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    eps: Optional[float] = None
    dividend_yield: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    beta: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StockInfo(BaseModel):
    ticker: str
    name: str
    price: float
    change: float
    change_pct: float
    volume: int
    avg_volume: Optional[int] = None
    market_cap: Optional[float] = None
    enterprise_value: Optional[float] = None
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    peg_ratio: Optional[float] = None
    price_to_book: Optional[float] = None
    price_to_sales: Optional[float] = None
    eps: Optional[float] = None
    eps_forward: Optional[float] = None
    dividend_yield: Optional[float] = None
    dividend_rate: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    beta: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    operating_margin: Optional[float] = None
    profit_margin: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    free_cashflow: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    employees: Optional[int] = None
    exchange: Optional[str] = None
    currency: Optional[str] = None


class PriceBar(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float] = None


class HistoricalData(BaseModel):
    ticker: str
    period: str
    interval: str
    bars: List[PriceBar]


# ─── Technical Analysis ──────────────────────────────────────────────────────

class IndicatorSignal(BaseModel):
    value: Optional[float]
    signal: str  # 'bullish', 'bearish', 'neutral'
    description: str
    formula: Optional[str] = None
    interpretation: Optional[str] = None


class TechnicalIndicators(BaseModel):
    ticker: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    rsi: Optional[IndicatorSignal] = None
    macd: Optional[Dict[str, Any]] = None
    adx: Optional[IndicatorSignal] = None
    atr: Optional[IndicatorSignal] = None
    bollinger_bands: Optional[Dict[str, Any]] = None
    keltner_channels: Optional[Dict[str, Any]] = None
    stochastic: Optional[Dict[str, Any]] = None
    ichimoku: Optional[Dict[str, Any]] = None
    supertrend: Optional[Dict[str, Any]] = None
    obv: Optional[IndicatorSignal] = None
    cmf: Optional[IndicatorSignal] = None
    mfi: Optional[IndicatorSignal] = None
    vwap: Optional[IndicatorSignal] = None
    support_levels: Optional[List[float]] = None
    resistance_levels: Optional[List[float]] = None
    volume_profile: Optional[List[Dict[str, float]]] = None
    trend: Optional[str] = None
    momentum: Optional[str] = None
    overall_signal: Optional[str] = None


# ─── Options Analysis ────────────────────────────────────────────────────────

class Greeks(BaseModel):
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    vanna: float
    charm: float
    vomma: float
    speed: float
    color: float
    zomma: float


class BSPrice(BaseModel):
    call_price: float
    put_price: float
    call_greeks: Greeks
    put_greeks: Greeks
    d1: float
    d2: float
    stock_price: float
    strike: float
    time_to_expiry: float
    risk_free_rate: float
    volatility: float


class OptionContract(BaseModel):
    strike: float
    expiry: str
    call_price: Optional[float] = None
    put_price: Optional[float] = None
    call_iv: Optional[float] = None
    put_iv: Optional[float] = None
    call_delta: Optional[float] = None
    put_delta: Optional[float] = None
    call_gamma: Optional[float] = None
    put_gamma: Optional[float] = None
    call_oi: Optional[int] = None
    put_oi: Optional[int] = None
    call_oi_change: Optional[int] = None
    put_oi_change: Optional[int] = None
    call_volume: Optional[int] = None
    put_volume: Optional[int] = None
    days_to_expiry: Optional[int] = None
    in_the_money_call: Optional[bool] = None
    in_the_money_put: Optional[bool] = None


class OptionsAnalysis(BaseModel):
    ticker: str
    spot_price: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    put_call_ratio: Optional[float] = None
    iv_rank: Optional[float] = None
    iv_percentile: Optional[float] = None
    current_iv: Optional[float] = None
    historical_vol_30d: Optional[float] = None
    historical_vol_60d: Optional[float] = None
    realized_vol: Optional[float] = None
    max_pain: Optional[float] = None
    gamma_exposure: Optional[float] = None
    gamma_squeeze_score: Optional[float] = None
    option_chain: Optional[List[OptionContract]] = None
    expiry_dates: Optional[List[str]] = None
    vol_skew: Optional[List[Dict[str, float]]] = None
    vol_surface: Optional[List[Dict[str, Any]]] = None


# ─── Fundamental Analysis ────────────────────────────────────────────────────

class IncomeStatement(BaseModel):
    year: str
    revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_income: Optional[float] = None
    net_income: Optional[float] = None
    ebitda: Optional[float] = None
    eps: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None


class BalanceSheet(BaseModel):
    year: str
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    total_equity: Optional[float] = None
    cash: Optional[float] = None
    total_debt: Optional[float] = None
    current_assets: Optional[float] = None
    current_liabilities: Optional[float] = None
    book_value_per_share: Optional[float] = None


class CashFlowStatement(BaseModel):
    year: str
    operating_cash_flow: Optional[float] = None
    capex: Optional[float] = None
    free_cash_flow: Optional[float] = None
    dividends_paid: Optional[float] = None


class DCFResult(BaseModel):
    intrinsic_value: float
    current_price: float
    margin_of_safety: float
    upside_downside: float
    wacc: float
    terminal_growth_rate: float
    enterprise_value: float
    stage1_value: float
    stage2_value: float
    terminal_value_pv: float
    assumptions: Dict[str, Any]


class FundamentalAnalysis(BaseModel):
    ticker: str
    income_statements: List[IncomeStatement]
    balance_sheets: List[BalanceSheet]
    cash_flows: List[CashFlowStatement]
    revenue_cagr_3y: Optional[float] = None
    eps_cagr_3y: Optional[float] = None
    fcf_cagr_3y: Optional[float] = None
    debt_to_equity: Optional[float] = None
    interest_coverage: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    roe: Optional[float] = None
    roce: Optional[float] = None
    roa: Optional[float] = None
    dcf: Optional[DCFResult] = None


# ─── Quantitative Analysis ───────────────────────────────────────────────────

class MonteCarloResult(BaseModel):
    simulations: int
    horizon_days: int
    current_price: float
    mean_price: float
    std_price: float
    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float
    probability_profit: float
    percentiles: Dict[str, float]
    sample_paths: List[List[float]]  # subset of paths for chart


class QuantMetrics(BaseModel):
    ticker: str
    period: str
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    treynor_ratio: Optional[float] = None
    calmar_ratio: Optional[float] = None
    omega_ratio: Optional[float] = None
    information_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    max_drawdown_duration: Optional[int] = None
    annualized_return: Optional[float] = None
    annualized_volatility: Optional[float] = None
    beta: Optional[float] = None
    alpha: Optional[float] = None
    capm_expected_return: Optional[float] = None
    var_95_1d: Optional[float] = None
    var_99_1d: Optional[float] = None
    cvar_95_1d: Optional[float] = None
    kelly_criterion: Optional[float] = None
    monte_carlo: Optional[MonteCarloResult] = None
    rolling_beta: Optional[List[Dict[str, Any]]] = None
    drawdown_series: Optional[List[Dict[str, Any]]] = None


# ─── Scoring Engine ──────────────────────────────────────────────────────────

class ScoreBreakdown(BaseModel):
    score: float  # 0-100
    grade: str    # A+, A, B+, B, C+, C, D, F
    signal: str   # bullish, bearish, neutral
    components: Dict[str, float]
    explanation: str


class CompositeScore(BaseModel):
    ticker: str
    overall_score: float
    overall_grade: str
    overall_signal: str
    fundamental_score: ScoreBreakdown
    technical_score: ScoreBreakdown
    quant_score: ScoreBreakdown
    options_score: ScoreBreakdown
    sentiment_score: ScoreBreakdown
    risk_score: ScoreBreakdown
    recommendation: str  # Strong Buy, Buy, Hold, Sell, Strong Sell
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ─── AI Insights ─────────────────────────────────────────────────────────────

class AIInsights(BaseModel):
    ticker: str
    rating: str
    rating_score: float
    pros: List[str]
    cons: List[str]
    risks: List[str]
    growth_drivers: List[str]
    valuation_commentary: str
    technical_trend: str
    institutional_positioning: str
    options_positioning: str
    summary: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ─── News ────────────────────────────────────────────────────────────────────

class NewsArticle(BaseModel):
    title: str
    source: str
    url: str
    published: Optional[datetime] = None
    summary: Optional[str] = None
    sentiment: Optional[str] = None  # bullish, bearish, neutral
    sentiment_score: Optional[float] = None


class NewsAnalysis(BaseModel):
    ticker: str
    articles: List[NewsArticle]
    overall_sentiment: str
    sentiment_score: float
    news_score: float
    ai_summary: str


# ─── Portfolio ───────────────────────────────────────────────────────────────

class PortfolioPosition(BaseModel):
    ticker: str
    shares: float
    avg_cost: float
    current_price: Optional[float] = None
    market_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None
    weight: Optional[float] = None


class PortfolioAnalysis(BaseModel):
    positions: List[PortfolioPosition]
    total_value: float
    total_cost: float
    total_pnl: float
    total_pnl_pct: float
    sharpe_ratio: Optional[float] = None
    volatility: Optional[float] = None
    beta: Optional[float] = None
    diversification_score: Optional[float] = None
    correlation_matrix: Optional[Dict[str, Dict[str, float]]] = None
    efficient_frontier: Optional[List[Dict[str, float]]] = None


# ─── Alerts ──────────────────────────────────────────────────────────────────

class Alert(BaseModel):
    id: Optional[str] = None
    ticker: str
    alert_type: str  # price, rsi, macd, volume, iv, gamma, gap
    condition: str   # above, below, crosses_up, crosses_down
    threshold: float
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    triggered_at: Optional[datetime] = None


# ─── Request Models ───────────────────────────────────────────────────────────

class BSRequest(BaseModel):
    stock_price: float = Field(gt=0)
    strike: float = Field(gt=0)
    time_to_expiry: float = Field(gt=0, description="Years to expiration")
    risk_free_rate: float = Field(default=0.0525)
    volatility: float = Field(gt=0, le=5.0)


class PortfolioRequest(BaseModel):
    positions: List[Dict[str, Any]]  # [{ticker, shares, avg_cost}]
