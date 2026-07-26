# QuantStock AI

**Institutional-grade stock research platform** — Bloomberg Terminal inspired, powered by quantitative finance, options analytics, and AI-driven insights.

---

## Architecture

```
quantstock-ai/
├── backend/              # FastAPI Python service
│   ├── app/
│   │   ├── main.py       # App entry point + middleware
│   │   ├── config.py     # Settings (env vars)
│   │   ├── core/
│   │   │   ├── cache.py  # Redis async cache layer
│   │   │   └── database.py
│   │   ├── services/     # Pure computation modules (no side effects)
│   │   │   ├── market_data.py         # yfinance: prices, quotes, options chain
│   │   │   ├── technical_analysis.py  # 12+ indicators with signals
│   │   │   ├── options_analysis.py    # Black-Scholes, 11 Greeks, GEX, Max Pain
│   │   │   ├── fundamental_analysis.py# DCF, WACC, financial ratios
│   │   │   ├── quant_analysis.py      # Sharpe/Sortino/VaR/Monte Carlo/Kelly
│   │   │   ├── scoring_engine.py      # Composite QuantScore™ (0–100)
│   │   │   └── ai_insights.py        # Rule-based AI insights generator
│   │   ├── routers/      # FastAPI route handlers
│   │   │   ├── stocks.py             # /stocks/* endpoints
│   │   │   └── portfolio.py          # /portfolio/analyze
│   │   └── plugins/      # Extension system
│   │       ├── base_plugin.py        # Abstract base for plugins
│   │       └── plugin_registry.py    # Auto-discovery + run-all
│   └── tests/
│       └── test_calculations.py      # 30+ unit tests
│
└── frontend/             # Next.js 14 TypeScript app
    ├── app/
    │   ├── page.tsx      # Home / search page
    │   └── stock/[ticker]/page.tsx  # Full analysis dashboard
    ├── components/
    │   ├── dashboard/    # StockHeader, MetricsGrid (18 KPIs)
    │   ├── charts/       # PriceChart (TradingView Lightweight Charts)
    │   ├── technical/    # TechnicalPanel — 12 indicators + S/R + Volume Profile
    │   ├── options/      # OptionsPanel — chain, skew, GEX, Max Pain
    │   ├── fundamental/  # FundamentalPanel — DCF, statements, ratios
    │   ├── quant/        # QuantPanel — ratios, Monte Carlo, Kelly
    │   ├── ai/           # AIInsightsPanel — pros/cons/risks/drivers
    │   └── scoring/      # ScoreCard — animated QuantScore™ gauge
    ├── lib/
    │   ├── api.ts        # Typed API client (axios)
    │   └── formatters.ts # Financial formatting utilities
    └── types/index.ts    # Complete TypeScript type definitions
```

---

## Quantitative Methods

### Options Analytics
| Formula | Implementation |
|---------|---------------|
| **Black-Scholes** `C = S·N(d₁) - K·e^{-rT}·N(d₂)` | `options_analysis.bs_price()` |
| **Implied Volatility** | Newton-Raphson solver (100 iterations, tol=1e-6) |
| **Greeks** Δ, Γ, Θ, ν, ρ, Vanna, Charm, Vomma, Speed, Color, Zomma | `calculate_greeks()` |
| **Max Pain** `Σ OI × intrinsic` | `calculate_max_pain()` |
| **GEX** `Σ (Call_OI - Put_OI) × Γ × S² × lot × 0.01` | `calculate_gex()` |
| **IV Rank** `(IV - IV_low) / (IV_high - IV_low) × 100` | `iv_rank()` |

### Risk Metrics
| Metric | Formula |
|--------|---------|
| **Sharpe** | `(Rp - Rf) / σp` |
| **Sortino** | `(Rp - Rf) / σ_downside` |
| **Calmar** | `Ann. Return / |Max Drawdown|` |
| **Omega** | `Σ gains / Σ losses` |
| **VaR 95%** | `Empirical 5th percentile (historical)` |
| **CVaR** | `E[L | L > VaR]` |
| **Kelly** | `f* = (p·b - q) / b` |
| **Monte Carlo** | GBM: `S(t+dt) = S(t)·exp((μ-σ²/2)dt + σ√dt·Z)` |

### Fundamental
| Metric | Notes |
|--------|-------|
| **DCF** | Two-stage (5yr + 5yr) + Gordon Growth terminal value |
| **WACC** | `(E/V)·Re + (D/V)·Rd·(1-T)`, cost of equity via CAPM |
| **CAGR** | `(End/Start)^{1/n} - 1` |

---

## Getting Started

### Docker (recommended)
```bash
cp .env.example .env
docker-compose up --build
```
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs

### Manual

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## API Endpoints

| Endpoint | Description | Cache TTL |
|----------|-------------|-----------|
| `GET /stocks/{ticker}/info` | Full quote + fundamentals | 60s |
| `GET /stocks/{ticker}/history?period=1Y` | OHLCV bars | 60–300s |
| `GET /stocks/{ticker}/technical` | 12 indicators with signals | 300s |
| `GET /stocks/{ticker}/options?expiry=2025-01-17` | Options chain + analytics | 120s |
| `GET /stocks/{ticker}/fundamental` | Statements + DCF + ratios | 3600s |
| `GET /stocks/{ticker}/quant` | Sharpe/VaR/Monte Carlo | 300s |
| `GET /stocks/{ticker}/score` | Composite QuantScore™ | 300s |
| `GET /stocks/{ticker}/insights` | AI-generated insights | 600s |
| `GET /stocks/{ticker}/full` | All of the above | 60s |
| `POST /portfolio/analyze` | Portfolio-level analytics | — |
| `POST /stocks/{ticker}/bs` | Black-Scholes calculator | — |
| `GET /plugins` | List active plugins | — |

---

## Plugin System

Add new analysis modules without touching existing code:

```python
# backend/app/plugins/modules/my_plugin.py
from app.plugins.base_plugin import BaseAnalysisPlugin

class VIXCorrelationPlugin(BaseAnalysisPlugin):
    name = "vix_correlation"
    description = "Correlates stock with VIX fear index"

    async def analyze(self, ticker: str, context: dict) -> dict:
        prices = context.get("stock_info", {}).get("price")
        # ... your analysis ...
        return {"vix_beta": 1.23, "interpretation": "..."}

# Auto-discovered on startup — no other files to modify
```

---

## Running Tests

```bash
cd backend
pip install pytest pytest-asyncio
pytest tests/test_calculations.py -v
```

Tests cover: Black-Scholes pricing, put-call parity, Greeks correctness, implied volatility solver round-trip, all risk ratios, drawdown calculations, Monte Carlo distributional properties, DCF monotonicity, CAGR formulas, and max-pain/PCR calculations.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React 18, TypeScript, TailwindCSS |
| Charts | TradingView Lightweight Charts (price), Recharts (indicators) |
| State | TanStack Query (server state), Zustand (UI state) |
| Backend | FastAPI, Python 3.11, Uvicorn |
| Data | yfinance, yahooquery, pandas |
| Quant | NumPy, SciPy, statsmodels, pandas-ta |
| Cache | Redis (async, per-endpoint TTLs) |
| Queue | Celery + Redis broker |
| Database | PostgreSQL + SQLAlchemy |
| Tests | pytest + pytest-asyncio |
| Deploy | Docker + docker-compose |
