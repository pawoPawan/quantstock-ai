'use client'

import { gradeColor, signalColor, recommendationColor, scoreColor } from '@/lib/formatters'
import type { CompositeScore, AIInsights } from '@/types'

const DIMENSION_LABELS: Record<string, string> = {
  fundamental_score: 'Fundamental',
  technical_score: 'Technical',
  quant_score: 'Quantitative',
  options_score: 'Options',
  sentiment_score: 'Sentiment',
  risk_score: 'Risk',
}

interface Props {
  score: CompositeScore
  insights: AIInsights
}

export default function ScoreCard({ score, insights }: Props) {
  const dimensions = [
    'fundamental_score', 'technical_score', 'quant_score',
    'options_score', 'sentiment_score', 'risk_score',
  ] as const

  return (
    <div className="card-elevated space-y-4">
      {/* Overall score */}
      <div className="text-center">
        <div className="section-title">QuantScore™</div>
        <div className="relative w-28 h-28 mx-auto my-3">
          <svg className="w-28 h-28 -rotate-90" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="42" stroke="#1a1a1a" strokeWidth="8" fill="none" />
            <circle
              cx="50" cy="50" r="42"
              stroke={scoreColor(score.overall_score)}
              strokeWidth="8"
              fill="none"
              strokeDasharray={`${2 * Math.PI * 42}`}
              strokeDashoffset={`${2 * Math.PI * 42 * (1 - score.overall_score / 100)}`}
              strokeLinecap="round"
              className="score-ring"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="font-mono font-bold text-2xl text-text-primary">{Math.round(score.overall_score)}</span>
            <span className={`font-mono text-xs font-bold ${gradeColor(score.overall_grade)}`}>{score.overall_grade}</span>
          </div>
        </div>

        <div className={`text-sm font-semibold ${recommendationColor(score.recommendation)}`}>
          {score.recommendation}
        </div>
        <div className={`text-xs mt-0.5 ${signalColor(score.overall_signal)}`}>
          {score.overall_signal?.replace('_', ' ').toUpperCase()}
        </div>
      </div>

      <div className="border-t border-bg-border" />

      {/* Dimension breakdown */}
      <div className="space-y-2.5">
        {dimensions.map(dim => {
          const d = score[dim]
          if (!d) return null
          return (
            <div key={dim}>
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs text-text-secondary">{DIMENSION_LABELS[dim]}</span>
                <div className="flex items-center gap-1.5">
                  <span className={`text-xs font-mono font-semibold ${gradeColor(d.grade)}`}>{d.grade}</span>
                  <span className="font-mono text-xs text-text-muted">{Math.round(d.score)}</span>
                </div>
              </div>
              <div className="h-1.5 bg-bg-primary rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{
                    width: `${d.score}%`,
                    background: scoreColor(d.score),
                  }}
                />
              </div>
            </div>
          )
        })}
      </div>

      <div className="border-t border-bg-border" />

      {/* Quick pros/cons */}
      {insights.pros.length > 0 && (
        <div>
          <div className="section-title text-bull mb-2">Strengths</div>
          <ul className="space-y-1.5">
            {insights.pros.slice(0, 3).map((pro, i) => (
              <li key={i} className="flex gap-2 text-xs text-text-secondary">
                <span className="text-bull mt-0.5 flex-shrink-0">+</span>
                <span>{pro}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {insights.cons.length > 0 && (
        <div>
          <div className="section-title text-bear mb-2">Risks</div>
          <ul className="space-y-1.5">
            {insights.cons.slice(0, 2).map((con, i) => (
              <li key={i} className="flex gap-2 text-xs text-text-secondary">
                <span className="text-bear mt-0.5 flex-shrink-0">-</span>
                <span>{con}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
