'use client'

import { useParams, useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { ArrowLeft, RefreshCw, AlertCircle } from 'lucide-react'
import { motion } from 'framer-motion'

import { stockApi } from '@/lib/api'
import StockHeader from '@/components/dashboard/StockHeader'
import MetricsGrid from '@/components/dashboard/MetricsGrid'
import PriceChart from '@/components/charts/PriceChart'
import ScoreCard from '@/components/scoring/ScoreCard'
import TechnicalPanel from '@/components/technical/TechnicalPanel'
import OptionsPanel from '@/components/options/OptionsPanel'
import FundamentalPanel from '@/components/fundamental/FundamentalPanel'
import QuantPanel from '@/components/quant/QuantPanel'
import AIInsightsPanel from '@/components/ai/AIInsightsPanel'
import SearchBar from '@/components/search/SearchBar'

const TABS = ['Overview', 'Technical', 'Options', 'Fundamental', 'Quant', 'AI Insights'] as const
type Tab = typeof TABS[number]

export default function StockPage() {
  const params = useParams()
  const router = useRouter()
  const ticker = (params.ticker as string).toUpperCase()
  const [activeTab, setActiveTab] = useState<Tab>('Overview')

  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['full-analysis', ticker],
    queryFn: () => stockApi.getFullAnalysis(ticker),
    staleTime: 60_000,
    refetchInterval: 300_000, // auto-refresh every 5 min
  })

  if (isLoading) return <LoadingScreen ticker={ticker} />
  if (error || !data) return <ErrorScreen ticker={ticker} error={error as Error} />

  const { stock_info, technical, fundamental, quant, options, score, insights, price_history } = data

  return (
    <div className="min-h-screen bg-bg-primary">
      {/* Top bar */}
      <div className="sticky top-0 z-50 bg-bg-primary/95 backdrop-blur border-b border-bg-border">
        <div className="max-w-screen-2xl mx-auto px-4 py-2 flex items-center gap-4">
          <button
            onClick={() => router.push('/')}
            className="p-2 hover:bg-bg-elevated rounded-lg transition-colors text-text-secondary hover:text-text-primary"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div className="flex-1 max-w-md">
            <SearchBar compact />
          </div>
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-text-secondary hover:text-text-primary border border-bg-border hover:border-brand/30 rounded-lg transition-all"
          >
            <RefreshCw className={`w-3 h-3 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      <div className="max-w-screen-2xl mx-auto px-4 py-4">
        {/* Stock header with price and key metrics */}
        <StockHeader info={stock_info} score={score} />

        {/* Main layout — sidebar + content */}
        <div className="mt-4 flex gap-4">
          {/* Score sidebar */}
          <div className="hidden xl:block w-72 flex-shrink-0">
            <ScoreCard score={score} insights={insights} />
          </div>

          {/* Main content */}
          <div className="flex-1 min-w-0">
            {/* Price chart */}
            <div className="card mb-4">
              <PriceChart ticker={ticker} history={price_history} />
            </div>

            {/* Quick metrics */}
            <MetricsGrid info={stock_info} />

            {/* Tabs */}
            <div className="mt-4">
              <div className="flex border-b border-bg-border mb-4 gap-1">
                {TABS.map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`px-4 py-2 text-xs font-medium transition-all border-b-2 -mb-px ${
                      activeTab === tab
                        ? 'border-brand text-brand'
                        : 'border-transparent text-text-muted hover:text-text-secondary'
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>

              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
              >
                {activeTab === 'Overview' && (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    <AIInsightsPanel insights={insights} score={score} compact />
                    <TechnicalPanel technical={technical} compact />
                  </div>
                )}
                {activeTab === 'Technical' && <TechnicalPanel technical={technical} />}
                {activeTab === 'Options' && <OptionsPanel options={options} ticker={ticker} spotPrice={stock_info.price} />}
                {activeTab === 'Fundamental' && <FundamentalPanel fundamental={fundamental} info={stock_info} />}
                {activeTab === 'Quant' && <QuantPanel quant={quant} />}
                {activeTab === 'AI Insights' && <AIInsightsPanel insights={insights} score={score} />}
              </motion.div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function LoadingScreen({ ticker }: { ticker: string }) {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="flex items-center justify-center gap-2 mb-4">
          <div className="w-2 h-2 bg-brand rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
          <div className="w-2 h-2 bg-brand rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <div className="w-2 h-2 bg-brand rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
        <p className="font-mono text-sm text-text-secondary">Analyzing {ticker}...</p>
        <p className="text-xs text-text-muted mt-1">Fetching market data, computing indicators</p>
      </div>
    </div>
  )
}

function ErrorScreen({ ticker, error }: { ticker: string; error: Error }) {
  const router = useRouter()
  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <div className="text-center max-w-sm">
        <div className="w-12 h-12 bg-bear-muted rounded-full flex items-center justify-center mx-auto mb-4">
          <AlertCircle className="w-6 h-6 text-bear" />
        </div>
        <h2 className="text-xl font-semibold text-text-primary mb-2">Failed to load {ticker}</h2>
        <p className="text-sm text-text-secondary mb-6">{error?.message || 'Ticker not found or data unavailable'}</p>
        <button
          onClick={() => router.push('/')}
          className="px-6 py-2.5 bg-brand hover:bg-brand-light text-white rounded-lg text-sm font-medium transition-colors"
        >
          Try another ticker
        </button>
      </div>
    </div>
  )
}
