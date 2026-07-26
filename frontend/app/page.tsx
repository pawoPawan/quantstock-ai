'use client'

import { useState, useCallback, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { Search, TrendingUp, Zap, BarChart3, Brain, Shield } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

const EXAMPLE_TICKERS = [
  { ticker: 'NVDA', name: 'NVIDIA Corp', change: '+2.4%', bull: true },
  { ticker: 'AAPL', name: 'Apple Inc', change: '+0.8%', bull: true },
  { ticker: 'TSLA', name: 'Tesla Inc', change: '-1.2%', bull: false },
  { ticker: 'MSFT', name: 'Microsoft', change: '+1.1%', bull: true },
  { ticker: 'RELIANCE.NS', name: 'Reliance Industries', change: '+0.5%', bull: true },
  { ticker: 'TCS.NS', name: 'Tata Consultancy', change: '+0.3%', bull: true },
  { ticker: 'INFY.NS', name: 'Infosys', change: '-0.4%', bull: false },
  { ticker: 'SPY', name: 'S&P 500 ETF', change: '+0.6%', bull: true },
]

const FEATURES = [
  { icon: BarChart3, title: 'Technical Analysis', desc: '15+ indicators: RSI, MACD, Bollinger, Ichimoku, SuperTrend, OBV, and more' },
  { icon: TrendingUp, title: 'Options Analytics', desc: 'Black-Scholes pricing, 11 Greeks, GEX, Max Pain, IV surface & volatility skew' },
  { icon: Zap, title: 'Quantitative Metrics', desc: 'Sharpe, Sortino, Calmar ratios, Monte Carlo, VaR/CVaR, Kelly Criterion' },
  { icon: Brain, title: 'AI Insights', desc: 'Composite QuantScore, rating rationale, pros/cons, and risk assessment' },
  { icon: Shield, title: 'Fundamental Analysis', desc: 'DCF valuation, multi-stage projections, WACC, margin of safety' },
  { icon: Search, title: 'Global Coverage', desc: 'US stocks, Indian markets (NSE/BSE), ETFs, and major indices' },
]

interface SearchResult { ticker: string; name: string; exchange: string; type: string }

export default function HomePage() {
  const router = useRouter()
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [suggestions, setSuggestions] = useState<SearchResult[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [activeIndex, setActiveIndex] = useState(-1)
  const searchRef = useRef<HTMLDivElement>(null)

  const navigate = useCallback((ticker: string) => {
    setLoading(true)
    setShowSuggestions(false)
    router.push(`/stock/${ticker.toUpperCase()}`)
  }, [router])

  // Debounced live search
  useEffect(() => {
    if (!query.trim() || query.length < 1) {
      setSuggestions([])
      setShowSuggestions(false)
      return
    }
    const timer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/stocks/search?q=${encodeURIComponent(query)}`)
        const { results } = await res.json()
        setSuggestions(results?.slice(0, 8) || [])
        setShowSuggestions(true)
        setActiveIndex(-1)
      } catch {
        setSuggestions([])
      }
    }, 250)
    return () => clearTimeout(timer)
  }, [query])

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node))
        setShowSuggestions(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showSuggestions || suggestions.length === 0) return
    if (e.key === 'ArrowDown') { e.preventDefault(); setActiveIndex(i => Math.min(i + 1, suggestions.length - 1)) }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActiveIndex(i => Math.max(i - 1, -1)) }
    else if (e.key === 'Escape') setShowSuggestions(false)
    else if (e.key === 'Enter' && activeIndex >= 0) { e.preventDefault(); navigate(suggestions[activeIndex].ticker) }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const q = query.trim()
    if (!q) return
    if (suggestions.length > 0) {
      navigate(activeIndex >= 0 ? suggestions[activeIndex].ticker : suggestions[0].ticker)
    } else {
      navigate(q)
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-bg-border px-6 py-4 flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-brand rounded flex items-center justify-center">
            <BarChart3 className="w-4 h-4 text-white" />
          </div>
          <span className="font-semibold text-text-primary tracking-tight">QuantStock AI</span>
        </div>
        <span className="text-xs font-mono px-2 py-0.5 bg-bg-elevated rounded border border-bg-border text-text-muted">
          Institutional Grade
        </span>
      </header>

      {/* Hero */}
      <main className="flex-1 flex flex-col items-center justify-center px-6 py-16">
        <motion.div
          className="text-center mb-12 max-w-3xl"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-brand/10 border border-brand/20 rounded-full text-xs text-brand mb-6">
            <Zap className="w-3 h-3" />
            Jane Street · Citadel · Two Sigma · Renaissance Tech methodology
          </div>
          <h1 className="text-5xl font-bold text-text-primary mb-4 leading-tight">
            Institutional Stock Research<br />
            <span className="text-brand">Powered by AI & Quant</span>
          </h1>
          <p className="text-lg text-text-secondary max-w-2xl mx-auto">
            Black-Scholes options analytics, 15+ technical indicators, DCF valuation,
            Monte Carlo simulation, and AI-driven insights — all in one platform.
          </p>
        </motion.div>

        {/* Search Box */}
        <motion.div
          className="w-full max-w-2xl mb-10"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <div ref={searchRef} className="relative">
            <form onSubmit={handleSubmit}>
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted z-10" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
                placeholder="Search by ticker or company — NVDA, Apple, Reliance..."
                className="w-full bg-bg-card border border-bg-border rounded-xl px-12 py-4 text-text-primary placeholder:text-text-muted font-mono text-sm focus:outline-none focus:border-brand/50 focus:ring-1 focus:ring-brand/30 transition-all"
                disabled={loading}
                autoFocus
                autoComplete="off"
              />
              <button
                type="submit"
                disabled={!query.trim() || loading}
                className="absolute right-3 top-1/2 -translate-y-1/2 px-4 py-2 bg-brand hover:bg-brand-light disabled:opacity-40 text-white rounded-lg text-sm font-medium transition-colors"
              >
                {loading ? 'Loading...' : 'Analyze →'}
              </button>
            </form>

            {/* Autocomplete dropdown */}
            <AnimatePresence>
              {showSuggestions && suggestions.length > 0 && (
                <motion.ul
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  transition={{ duration: 0.1 }}
                  className="absolute z-50 w-full mt-1 bg-bg-card border border-bg-border rounded-xl overflow-hidden shadow-xl"
                >
                  {suggestions.map((s, i) => (
                    <li
                      key={s.ticker}
                      onMouseEnter={() => setActiveIndex(i)}
                      onMouseDown={() => navigate(s.ticker)}
                      className={`flex items-center gap-3 px-4 py-3 cursor-pointer transition-colors ${
                        i === activeIndex ? 'bg-brand/10' : 'hover:bg-bg-elevated'
                      } ${i !== 0 ? 'border-t border-bg-border' : ''}`}
                    >
                      <span className="font-mono font-semibold text-brand text-sm w-28 shrink-0">{s.ticker}</span>
                      <span className="text-text-primary text-sm truncate flex-1">{s.name}</span>
                      <span className="text-text-muted text-xs shrink-0">{s.exchange}</span>
                    </li>
                  ))}
                </motion.ul>
              )}
            </AnimatePresence>
          </div>
        </motion.div>

        {/* Quick tickers */}
        <motion.div
          className="flex flex-wrap justify-center gap-2 mb-16"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          {EXAMPLE_TICKERS.map((item) => (
            <button
              key={item.ticker}
              onClick={() => navigate(item.ticker)}
              className="group flex items-center gap-2 px-3 py-1.5 bg-bg-card hover:bg-bg-elevated border border-bg-border rounded-lg transition-all text-sm"
            >
              <span className="font-mono font-medium text-text-primary">{item.ticker}</span>
              <span className="text-xs text-text-muted group-hover:text-text-secondary transition-colors">{item.name}</span>
              <span className={`text-xs font-mono ${item.bull ? 'text-bull' : 'text-bear'}`}>{item.change}</span>
            </button>
          ))}
        </motion.div>

        {/* Features Grid */}
        <motion.div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-5xl w-full"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          {FEATURES.map((f) => (
            <div key={f.title} className="card group hover:border-brand/30 transition-colors">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-brand/10 rounded-lg flex items-center justify-center flex-shrink-0">
                  <f.icon className="w-4 h-4 text-brand" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-text-primary mb-1">{f.title}</h3>
                  <p className="text-xs text-text-muted leading-relaxed">{f.desc}</p>
                </div>
              </div>
            </div>
          ))}
        </motion.div>
      </main>

      {/* Footer */}
      <footer className="border-t border-bg-border px-6 py-4 text-center text-xs text-text-muted">
        QuantStock AI — For educational purposes only. Not financial advice.
      </footer>
    </div>
  )
}
