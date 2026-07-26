'use client'

import { CheckCircle2, XCircle, AlertTriangle, TrendingUp, Brain, Shield, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import { recommendationColor, signalColor, gradeColor, scoreColor } from '@/lib/formatters'
import type { AIInsights, CompositeScore } from '@/types'

interface Props {
  insights: AIInsights
  score: CompositeScore
  compact?: boolean
}

export default function AIInsightsPanel({ insights, score, compact }: Props) {
  const [expanded, setExpanded] = useState(!compact)

  // Guard: if insights or score failed to load, show a minimal placeholder
  if (!insights || !insights.rating) {
    return (
      <div className="card text-text-muted text-sm text-center py-8">
        AI insights unavailable for this ticker (no company financials or options data).
      </div>
    )
  }

  const ratingColors: Record<string, string> = {
    'Strong Buy': 'text-bull border-bull',
    'Buy': 'text-[#69F0AE] border-[#69F0AE]',
    'Hold': 'text-warn border-warn',
    'Sell': 'text-[#FF7979] border-[#FF7979]',
    'Strong Sell': 'text-bear border-bear',
  }
  const ratingBg: Record<string, string> = {
    'Strong Buy': 'bg-bull/10',
    'Buy': 'bg-[#69F0AE]/10',
    'Hold': 'bg-warn/10',
    'Sell': 'bg-[#FF7979]/10',
    'Strong Sell': 'bg-bear/10',
  }

  return (
    <div className="space-y-4">
      {/* Summary + Rating */}
      <div className="card">
        <div className="flex items-start gap-4 mb-4">
          <div className={`flex-shrink-0 px-4 py-2 rounded-lg border ${ratingColors[insights.rating] || 'text-text-secondary border-bg-border'} ${ratingBg[insights.rating] || ''}`}>
            <div className="text-xs text-text-muted mb-1">Rating</div>
            <div className="font-bold text-base">{insights.rating}</div>
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <Brain className="w-4 h-4 text-brand" />
              <span className="text-xs font-semibold text-brand uppercase tracking-wider">AI Analysis</span>
            </div>
            <p className="text-sm text-text-secondary leading-relaxed">{insights.summary}</p>
          </div>
        </div>

        {/* Score breakdown mini grid */}
        <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
          {[
            { label: 'Fundamental', dim: score?.fundamental_score },
            { label: 'Technical', dim: score?.technical_score },
            { label: 'Quant', dim: score?.quant_score },
            { label: 'Options', dim: score?.options_score },
            { label: 'Sentiment', dim: score?.sentiment_score },
            { label: 'Risk', dim: score?.risk_score },
          ].filter(({ dim }) => dim != null).map(({ label, dim }) => (
            <div key={label} className="text-center bg-bg-elevated rounded-lg p-2">
              <div className="text-[10px] text-text-muted mb-1">{label}</div>
              <div className="font-mono font-bold text-sm" style={{ color: scoreColor(dim!.score) }}>
                {Math.round(dim!.score)}
              </div>
              <div className={`text-[10px] font-semibold ${gradeColor(dim!.grade)}`}>{dim!.grade}</div>
            </div>
          ))}
        </div>

        {compact && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="w-full flex items-center justify-center gap-1 mt-3 text-xs text-text-muted hover:text-text-secondary transition-colors"
          >
            {expanded ? <><ChevronUp className="w-3 h-3" /> Less</> : <><ChevronDown className="w-3 h-3" /> More insights</>}
          </button>
        )}
      </div>

      {expanded && (
        <>
          {/* Pros */}
          {(insights.pros?.length ?? 0) > 0 && (
            <div className="card">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle2 className="w-4 h-4 text-bull" />
                <span className="text-sm font-semibold text-bull">Strengths & Catalysts</span>
              </div>
              <ul className="space-y-2">
                {insights.pros.map((pro, i) => (
                  <li key={i} className="flex gap-2 text-sm text-text-secondary">
                    <span className="text-bull font-bold mt-0.5 flex-shrink-0">+</span>
                    {pro}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Cons */}
          {(insights.cons?.length ?? 0) > 0 && (
            <div className="card">
              <div className="flex items-center gap-2 mb-3">
                <XCircle className="w-4 h-4 text-bear" />
                <span className="text-sm font-semibold text-bear">Weaknesses & Concerns</span>
              </div>
              <ul className="space-y-2">
                {insights.cons.map((con, i) => (
                  <li key={i} className="flex gap-2 text-sm text-text-secondary">
                    <span className="text-bear font-bold mt-0.5 flex-shrink-0">-</span>
                    {con}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Risks */}
          {(insights.risks?.length ?? 0) > 0 && (
            <div className="card border-warn/20">
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle className="w-4 h-4 text-warn" />
                <span className="text-sm font-semibold text-warn">Key Risks</span>
              </div>
              <ul className="space-y-2">
                {insights.risks.map((risk, i) => (
                  <li key={i} className="flex gap-2 text-sm text-text-secondary">
                    <span className="text-warn font-bold mt-0.5 flex-shrink-0">!</span>
                    {risk}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Growth Drivers */}
          {(insights.growth_drivers?.length ?? 0) > 0 && (
            <div className="card">
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="w-4 h-4 text-brand" />
                <span className="text-sm font-semibold text-brand">Growth Drivers</span>
              </div>
              <ul className="space-y-2">
                {insights.growth_drivers.map((d, i) => (
                  <li key={i} className="flex gap-2 text-sm text-text-secondary">
                    <span className="text-brand font-bold mt-0.5 flex-shrink-0">→</span>
                    {d}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Valuation + Technical + Options commentary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="card">
              <div className="section-title mb-2">Valuation</div>
              <p className="text-xs text-text-secondary leading-relaxed">{insights.valuation_commentary}</p>
            </div>
            <div className="card">
              <div className="section-title mb-2">Technical Trend</div>
              <p className="text-xs text-text-secondary leading-relaxed">{insights.technical_trend}</p>
            </div>
            <div className="card">
              <div className="section-title mb-2">Options Positioning</div>
              <p className="text-xs text-text-secondary leading-relaxed">{insights.options_positioning}</p>
            </div>
          </div>

          {/* Institutional positioning */}
          <div className="card">
            <div className="flex items-center gap-2 mb-2">
              <Shield className="w-4 h-4 text-text-muted" />
              <span className="section-title">Institutional Positioning</span>
            </div>
            <p className="text-sm text-text-secondary">{insights.institutional_positioning}</p>
          </div>
        </>
      )}

      {/* Disclaimer */}
      <div className="text-xs text-text-muted text-center px-4">
        AI insights are generated algorithmically from quantitative data. Not financial advice.
        Always conduct your own due diligence before making investment decisions.
      </div>
    </div>
  )
}
