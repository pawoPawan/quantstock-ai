import axios from 'axios'
import type { FullAnalysis, HistoricalData, TechnicalAnalysis, FundamentalAnalysis, QuantAnalysis, OptionsAnalysis, CompositeScore, AIInsights, SearchResult } from '@/types'

const API_URL = typeof window !== 'undefined'
  ? '/api'
  : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')

const api = axios.create({
  baseURL: API_URL,
  timeout: 60_000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    const msg = err.response?.data?.detail || err.message || 'API error'
    return Promise.reject(new Error(msg))
  },
)

export const stockApi = {
  search: (q: string): Promise<{ results: SearchResult[] }> =>
    api.get(`/stocks/search?q=${encodeURIComponent(q)}`).then(r => r.data),

  getInfo: (ticker: string) =>
    api.get(`/stocks/${ticker}/info`).then(r => r.data),

  getHistory: (ticker: string, period = '1Y', interval?: string): Promise<HistoricalData> =>
    api.get(`/stocks/${ticker}/history`, { params: { period, interval } }).then(r => r.data),

  getTechnical: (ticker: string, period = '1Y'): Promise<TechnicalAnalysis> =>
    api.get(`/stocks/${ticker}/technical`, { params: { period } }).then(r => r.data),

  getFundamental: (ticker: string): Promise<FundamentalAnalysis> =>
    api.get(`/stocks/${ticker}/fundamental`).then(r => r.data),

  getQuant: (ticker: string, period = '2Y'): Promise<QuantAnalysis> =>
    api.get(`/stocks/${ticker}/quant`, { params: { period } }).then(r => r.data),

  getOptions: (ticker: string, expiry?: string): Promise<OptionsAnalysis> =>
    api.get(`/stocks/${ticker}/options`, { params: { expiry } }).then(r => r.data),

  getScore: (ticker: string): Promise<CompositeScore> =>
    api.get(`/stocks/${ticker}/score`).then(r => r.data),

  getInsights: (ticker: string): Promise<AIInsights> =>
    api.get(`/stocks/${ticker}/insights`).then(r => r.data),

  getFullAnalysis: (ticker: string): Promise<FullAnalysis> =>
    api.get(`/stocks/${ticker}/full`).then(r => r.data),

  blackScholes: (params: {
    stock_price: number
    strike: number
    time_to_expiry: number
    risk_free_rate?: number
    volatility: number
  }) => api.post(`/stocks/BS/bs`, null, { params }).then(r => r.data),
}

export const portfolioApi = {
  analyze: (positions: { ticker: string; shares: number; avg_cost: number }[]) =>
    api.post('/portfolio/analyze', positions).then(r => r.data),
}

export default api
