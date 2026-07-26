// ─── Market Data ─────────────────────────────────────────────────────────────

export interface StockInfo {
  ticker: string
  name: string
  price: number
  change: number
  change_pct: number
  volume: number
  avg_volume?: number
  market_cap?: number
  enterprise_value?: number
  pe_ratio?: number
  forward_pe?: number
  peg_ratio?: number
  price_to_book?: number
  price_to_sales?: number
  eps?: number
  eps_forward?: number
  dividend_yield?: number
  dividend_rate?: number
  week_52_high?: number
  week_52_low?: number
  beta?: number
  roe?: number
  roa?: number
  revenue_growth?: number
  earnings_growth?: number
  operating_margin?: number
  profit_margin?: number
  gross_margins?: number
  debt_to_equity?: number
  current_ratio?: number
  free_cashflow?: number
  sector?: string
  industry?: string
  country?: string
  website?: string
  description?: string
  employees?: number
  exchange?: string
  currency?: string
  shares_outstanding?: number
  insider_ownership?: number
  institutional_ownership?: number
  short_ratio?: number
  short_percent?: number
}

export interface PriceBar {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface HistoricalData {
  ticker: string
  period: string
  interval: string
  bars: PriceBar[]
}

// ─── Technical Analysis ───────────────────────────────────────────────────────

export interface IndicatorSignal {
  value?: number | null
  signal: 'bullish' | 'bearish' | 'neutral'
  description?: string
  formula?: string
  interpretation?: string
  series?: (number | null)[]
}

export interface TechnicalAnalysis {
  ticker?: string
  rsi?: IndicatorSignal & { value: number }
  macd?: {
    macd: number
    signal: number
    histogram: number
    trend: 'bullish' | 'bearish'
    crossover: string
    formula: string
    macd_series: number[]
    signal_series: number[]
    histogram_series: number[]
  }
  adx?: {
    value: number
    plus_di: number
    minus_di: number
    signal: string
    trend_strength: 'strong' | 'moderate' | 'weak'
    description: string
  }
  atr?: { value: number; pct_of_price: number; signal: string; description: string; interpretation: string }
  bollinger_bands?: {
    upper: number
    middle: number
    lower: number
    bandwidth: number
    pct_b: number
    signal: string
    squeeze: boolean
    upper_series: number[]
    lower_series: number[]
    middle_series: number[]
  }
  keltner_channels?: { upper: number; middle: number; lower: number; signal: string }
  stochastic?: { k: number; d: number; signal: string; overbought: boolean; oversold: boolean }
  ichimoku?: { tenkan: number; kijun: number; senkou_a?: number; senkou_b?: number; signal: string; above_cloud: boolean }
  supertrend?: { value: number; direction: number; signal: string }
  obv?: { value: number; ema20: number; signal: string; series?: number[] }
  cmf?: { value: number; signal: string }
  mfi?: { value: number; signal: string; overbought: boolean; oversold: boolean }
  vwap?: { value: number; signal: string; series?: number[] }
  support_levels?: number[]
  resistance_levels?: number[]
  volume_profile?: { price_level: number; volume: number; volume_pct: number }[]
  overall_signal?: string
  signal_counts?: { bullish: number; bearish: number; neutral: number }
  close_series?: number[]
  volume_series?: number[]
}

// ─── Options Analysis ─────────────────────────────────────────────────────────

export interface Greeks {
  delta: number
  gamma: number
  theta: number
  vega: number
  rho: number
  vanna: number
  charm: number
  vomma: number
  speed: number
  color: number
  zomma: number
}

export interface BSAnalysis {
  call_price: number
  put_price: number
  call_greeks: Greeks
  put_greeks: Greeks
  d1: number
  d2: number
  stock_price: number
  strike: number
  time_to_expiry: number
  risk_free_rate: number
  volatility: number
  moneyness: number
}

export interface OptionContract {
  strike: number
  expiry: string
  call_price?: number
  put_price?: number
  call_iv?: number
  put_iv?: number
  call_delta?: number
  put_delta?: number
  call_gamma?: number
  call_oi?: number
  put_oi?: number
  call_volume?: number
  put_volume?: number
  days_to_expiry?: number
  in_the_money_call?: boolean
  in_the_money_put?: boolean
}

export interface PutCallRatio {
  pcr_oi: number
  pcr_volume: number
  total_call_oi: number
  total_put_oi: number
  signal: string
  interpretation: string
}

export interface OptionsAnalysis {
  ticker: string
  spot_price: number
  put_call_ratio?: PutCallRatio
  iv_rank?: number
  iv_percentile?: number
  current_iv?: number
  historical_vol_30d?: number
  historical_vol_60d?: number
  realized_vol?: number
  max_pain?: number
  gamma_exposure?: number
  gamma_squeeze_score?: number
  dealer_positioning?: string
  squeeze_risk?: string
  gex_by_strike?: { strike: number; gex: number }[]
  option_chain?: OptionContract[]
  expiry_dates?: string[]
  selected_expiry?: string
  vol_skew?: { strike: number; moneyness: number; iv: number; log_moneyness: number }[]
}

// ─── Fundamental Analysis ─────────────────────────────────────────────────────

export interface IncomeStatement {
  year: string
  revenue?: number
  gross_profit?: number
  operating_income?: number
  net_income?: number
  ebitda?: number
  eps?: number
  gross_margin?: number
  operating_margin?: number
  net_margin?: number
}

export interface BalanceSheet {
  year: string
  total_assets?: number
  total_liabilities?: number
  total_equity?: number
  cash?: number
  total_debt?: number
  current_assets?: number
  current_liabilities?: number
  book_value_per_share?: number
  debt_to_equity?: number
  current_ratio?: number
}

export interface CashFlowStatement {
  year: string
  operating_cash_flow?: number
  capex?: number
  free_cash_flow?: number
  dividends_paid?: number
}

export interface DCFResult {
  intrinsic_value: number
  current_price: number
  margin_of_safety: number
  upside_downside: number
  upside_pct: number
  enterprise_value: number
  equity_value: number
  stage1_value: number
  stage2_value: number
  terminal_value: number
  terminal_value_pv: number
  tv_pct_of_ev: number
  wacc: number
  terminal_growth_rate: number
  assumptions: Record<string, number>
  stage1_projections: { year: number; fcf: number; pv: number }[]
  stage2_projections: { year: number; fcf: number; pv: number }[]
}

export interface FundamentalAnalysis {
  ticker: string
  income_statements: IncomeStatement[]
  balance_sheets: BalanceSheet[]
  cash_flows: CashFlowStatement[]
  ratios: Record<string, number>
  dcf?: DCFResult
  roe?: number
  roa?: number
  roce?: number
  net_margin?: number
  operating_margin?: number
  revenue_cagr_3y?: number
  eps_cagr_3y?: number
  debt_to_equity?: number
  current_ratio?: number
  wacc?: number
}

// ─── Quantitative Analysis ────────────────────────────────────────────────────

export interface MonteCarloResult {
  simulations: number
  horizon_days: number
  current_price: number
  mean_price: number
  std_price: number
  var_95: number
  var_99: number
  cvar_95: number
  cvar_99: number
  probability_profit: number
  expected_return_pct: number
  percentiles: Record<string, number>
  sample_paths: number[][]
}

export interface QuantAnalysis {
  ticker: string
  period: string
  annualized_return: number
  annualized_return_pct: number
  annualized_volatility: number
  annualized_volatility_pct: number
  sharpe_ratio?: number
  sortino_ratio?: number
  treynor_ratio?: number
  calmar_ratio?: number
  omega_ratio?: number
  max_drawdown?: number
  max_drawdown_pct?: number
  max_drawdown_duration?: number
  recovery_days?: number
  beta?: number
  alpha?: number
  r_squared?: number
  correlation?: number
  capm_expected_return?: number
  var_95_1d?: number
  var_99_1d?: number
  cvar_95_1d?: number
  kelly_criterion?: {
    kelly_pct: number
    half_kelly_pct: number
    win_rate: number
    avg_win_loss_ratio: number
    interpretation: string
  }
  monte_carlo?: MonteCarloResult
  drawdown_series?: number[]
  rolling_beta?: { index: number; beta: number }[]
}

// ─── Scoring ─────────────────────────────────────────────────────────────────

export interface ScoreBreakdown {
  score: number
  grade: string
  signal: string
  components: Record<string, number>
  explanation: string
}

export interface CompositeScore {
  ticker: string
  overall_score: number
  overall_grade: string
  overall_signal: string
  recommendation: string
  fundamental_score: ScoreBreakdown
  technical_score: ScoreBreakdown
  quant_score: ScoreBreakdown
  options_score: ScoreBreakdown
  sentiment_score: ScoreBreakdown
  risk_score: ScoreBreakdown
  weights: Record<string, number>
}

// ─── AI Insights ─────────────────────────────────────────────────────────────

export interface AIInsights {
  ticker: string
  rating: string
  rating_score: number
  pros: string[]
  cons: string[]
  risks: string[]
  growth_drivers: string[]
  valuation_commentary: string
  technical_trend: string
  institutional_positioning: string
  options_positioning: string
  summary: string
  sector?: string
}

// ─── Full Analysis ─────────────────────────────────────────────────────────────

export interface FullAnalysis {
  ticker: string
  stock_info: StockInfo
  technical: TechnicalAnalysis
  fundamental: FundamentalAnalysis
  quant: QuantAnalysis
  options?: OptionsAnalysis
  score: CompositeScore
  insights: AIInsights
  price_history?: HistoricalData
}

// ─── Portfolio ────────────────────────────────────────────────────────────────

export interface PortfolioPosition {
  ticker: string
  shares: number
  avg_cost: number
  current_price?: number
  market_value?: number
  cost_basis?: number
  unrealized_pnl?: number
  unrealized_pnl_pct?: number
  weight?: number
  name?: string
  sector?: string
}

// ─── Watchlist ────────────────────────────────────────────────────────────────

export interface WatchlistItem {
  ticker: string
  name?: string
  price?: number
  change?: number
  change_pct?: number
  volume?: number
  alert?: boolean
}

// ─── Search ───────────────────────────────────────────────────────────────────

export interface SearchResult {
  ticker: string
  name: string
  exchange?: string
  type?: string
}
