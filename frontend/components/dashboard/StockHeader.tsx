'use client'

import { TrendingUp, TrendingDown, Globe, Building2 } from 'lucide-react'
import { fmtPrice, fmtChange, fmtPct, fmtMarketCap, signColor, recommendationColor } from '@/lib/formatters'
import type { StockInfo, CompositeScore } from '@/types'

interface Props {
  info: StockInfo
  score: CompositeScore
}

export default function StockHeader({ info, score }: Props) {
  const isUp = info.change >= 0
  const recColor = recommendationColor(score.recommendation)

  return (
    <div className="card">
      <div className="flex flex-col lg:flex-row lg:items-center gap-4 justify-between">
        {/* Left — Name + Price */}
        <div className="flex items-start gap-4">
          {/* Ticker badge */}
          <div className="w-14 h-14 bg-brand/10 border border-brand/20 rounded-xl flex items-center justify-center flex-shrink-0">
            <span className="font-mono font-bold text-brand text-xs text-center leading-tight px-1">
              {info.ticker.replace('.NS', '').replace('.BO', '').slice(0, 4)}
            </span>
          </div>

          <div>
            <h1 className="text-xl font-bold text-text-primary">{info.name}</h1>
            <div className="flex items-center gap-2 mt-0.5 flex-wrap">
              <span className="font-mono text-xs text-text-muted">{info.ticker}</span>
              {info.exchange && (
                <span className="text-xs text-text-muted border border-bg-border rounded px-1.5 py-0.5">{info.exchange}</span>
              )}
              {info.sector && (
                <span className="flex items-center gap-1 text-xs text-text-muted">
                  <Building2 className="w-3 h-3" />
                  {info.sector}
                </span>
              )}
              {info.country && (
                <span className="flex items-center gap-1 text-xs text-text-muted">
                  <Globe className="w-3 h-3" />
                  {info.country}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Center — Price */}
        <div className="flex items-center gap-6">
          <div>
            <div className="font-mono text-3xl font-bold text-text-primary">
              {fmtPrice(info.price)}
            </div>
            <div className={`flex items-center gap-1 mt-1 font-mono text-sm ${signColor(info.change)}`}>
              {isUp ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              <span>{fmtChange(info.change)}</span>
              <span>({fmtPct(info.change_pct)})</span>
            </div>
          </div>

          <div className="h-12 w-px bg-bg-border" />

          <div>
            <div className="text-xs text-text-muted mb-1">Market Cap</div>
            <div className="font-mono font-semibold text-text-primary">{fmtMarketCap(info.market_cap)}</div>
          </div>

          {info.week_52_high && info.week_52_low && (
            <>
              <div className="h-12 w-px bg-bg-border hidden md:block" />
              <div className="hidden md:block">
                <div className="text-xs text-text-muted mb-1.5">52-Week Range</div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-bear">{fmtPrice(info.week_52_low)}</span>
                  <div className="relative w-24 h-1.5 bg-bg-elevated rounded-full overflow-hidden">
                    <div
                      className="absolute h-full bg-brand rounded-full"
                      style={{ width: `${((info.price - info.week_52_low) / (info.week_52_high - info.week_52_low)) * 100}%` }}
                    />
                  </div>
                  <span className="text-xs font-mono text-bull">{fmtPrice(info.week_52_high)}</span>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Right — Score + Recommendation */}
        <div className="flex items-center gap-4">
          <div className="text-center">
            <div className="text-xs text-text-muted mb-1">QuantScore</div>
            <div className="relative w-16 h-16">
              <svg className="w-16 h-16 -rotate-90" viewBox="0 0 64 64">
                <circle cx="32" cy="32" r="26" stroke="#1a1a1a" strokeWidth="6" fill="none" />
                <circle
                  cx="32" cy="32" r="26"
                  stroke={score.overall_score >= 65 ? '#00C853' : score.overall_score >= 40 ? '#FFB800' : '#FF3D3D'}
                  strokeWidth="6"
                  fill="none"
                  strokeDasharray={`${2 * Math.PI * 26}`}
                  strokeDashoffset={`${2 * Math.PI * 26 * (1 - score.overall_score / 100)}`}
                  strokeLinecap="round"
                  className="score-ring"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="font-mono font-bold text-sm text-text-primary">{Math.round(score.overall_score)}</span>
                <span className="font-mono text-[9px] text-text-muted">{score.overall_grade}</span>
              </div>
            </div>
          </div>

          <div className="text-center">
            <div className="text-xs text-text-muted mb-2">Recommendation</div>
            <div className={`font-semibold text-sm ${recColor}`}>{score.recommendation}</div>
          </div>
        </div>
      </div>
    </div>
  )
}
