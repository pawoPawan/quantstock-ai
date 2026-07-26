'use client'

import { useState } from 'react'
import { fmt, fmtPrice, fmtPct, signalBadgeClass, signColor } from '@/lib/formatters'
import type { OptionsAnalysis, OptionContract } from '@/types'
import { useQuery } from '@tanstack/react-query'
import { stockApi } from '@/lib/api'
import {
  ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, Tooltip, LineChart, Line, ReferenceLine,
} from 'recharts'

interface Props {
  options?: OptionsAnalysis
  ticker: string
  spotPrice: number
}

export default function OptionsPanel({ options: initialOptions, ticker, spotPrice }: Props) {
  const [selectedExpiry, setSelectedExpiry] = useState(initialOptions?.selected_expiry)

  const { data: options = initialOptions } = useQuery({
    queryKey: ['options', ticker, selectedExpiry],
    queryFn: () => stockApi.getOptions(ticker, selectedExpiry),
    enabled: !!selectedExpiry && selectedExpiry !== initialOptions?.selected_expiry,
    initialData: initialOptions,
  })

  if (!options) return <div className="card text-text-muted text-sm">Options data unavailable</div>

  const chain = options.option_chain || []
  const pcr = options.put_call_ratio
  const skew = options.vol_skew || []

  return (
    <div className="space-y-4">
      {/* Key Metrics row */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        <MetricBox label="Put/Call Ratio" value={fmt(pcr?.pcr_oi, 3)} color={pcr?.pcr_oi && pcr.pcr_oi > 1 ? 'text-bear' : 'text-bull'} note={pcr?.signal} />
        <MetricBox label="IV Rank" value={options.iv_rank !== undefined ? `${Math.round(options.iv_rank)}%` : '—'} color={options.iv_rank && options.iv_rank > 75 ? 'text-bear' : options.iv_rank && options.iv_rank < 25 ? 'text-bull' : 'text-warn'} />
        <MetricBox label="IV Percentile" value={options.iv_percentile !== undefined ? `${Math.round(options.iv_percentile)}th` : '—'} />
        <MetricBox label="Implied Vol" value={options.current_iv !== undefined ? `${fmt(options.current_iv)}%` : '—'} />
        <MetricBox label="Hist Vol 30D" value={options.historical_vol_30d !== undefined ? `${fmt(options.historical_vol_30d)}%` : '—'} />
        <MetricBox label="Max Pain" value={fmtPrice(options.max_pain)} note={options.max_pain ? `${((options.max_pain - spotPrice) / spotPrice * 100).toFixed(1)}% from spot` : undefined} />
      </div>

      {/* GEX + PCR row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="card">
          <div className="section-title mb-2">Gamma Exposure</div>
          <div className={`font-mono text-2xl font-bold ${(options.gamma_exposure ?? 0) > 0 ? 'text-bull' : 'text-bear'}`}>
            ${fmt(options.gamma_exposure, 2)}B
          </div>
          <div className="text-xs text-text-muted mt-1">{options.dealer_positioning?.replace('_', ' ')} positioning</div>
          <div className="text-xs mt-2">
            Squeeze Risk: <span className={options.squeeze_risk === 'high' ? 'text-bear' : options.squeeze_risk === 'moderate' ? 'text-warn' : 'text-bull'}>
              {options.squeeze_risk?.toUpperCase()}
            </span>
          </div>
          {options.gamma_squeeze_score !== undefined && (
            <div className="mt-2">
              <div className="flex justify-between text-xs text-text-muted mb-1">
                <span>Gamma Squeeze Score</span>
                <span>{Math.round(options.gamma_squeeze_score)}/100</span>
              </div>
              <div className="h-1.5 bg-bg-primary rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${options.gamma_squeeze_score}%`,
                    background: options.gamma_squeeze_score > 60 ? '#FF3D3D' : '#FFB800',
                  }}
                />
              </div>
            </div>
          )}
        </div>

        <div className="card">
          <div className="section-title mb-2">Sentiment</div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-text-muted">PCR (OI)</span>
              <span className={`font-mono ${pcr?.pcr_oi && pcr.pcr_oi > 1.2 ? 'text-bear' : 'text-bull'}`}>{fmt(pcr?.pcr_oi, 3)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">PCR (Vol)</span>
              <span className="font-mono">{fmt(pcr?.pcr_volume, 3)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">Total Call OI</span>
              <span className="font-mono text-bull">{(pcr?.total_call_oi || 0).toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">Total Put OI</span>
              <span className="font-mono text-bear">{(pcr?.total_put_oi || 0).toLocaleString()}</span>
            </div>
          </div>
          {pcr && (
            <div className={`mt-3 text-xs ${signalBadgeClass(pcr.signal)}`}>
              {pcr.interpretation}
            </div>
          )}
        </div>

        {/* Vol Skew chart */}
        <div className="card">
          <div className="section-title mb-2">Volatility Skew</div>
          {skew.length > 0 ? (
            <ResponsiveContainer width="100%" height={120}>
              <LineChart data={skew}>
                <XAxis dataKey="moneyness" tickFormatter={v => `${(v * 100).toFixed(0)}%`} tick={{ fontSize: 10, fill: '#666' }} />
                <YAxis dataKey="iv" tickFormatter={v => `${v}%`} width={35} tick={{ fontSize: 10, fill: '#666' }} />
                <ReferenceLine x={1} stroke="#666" strokeDasharray="3 3" />
                <Tooltip
                  contentStyle={{ background: '#141414', border: '1px solid #242424', borderRadius: 6, fontSize: 11 }}
                  formatter={(v: number) => [`${v?.toFixed(1)}%`, 'IV']}
                  labelFormatter={(v) => `Moneyness: ${(Number(v) * 100).toFixed(0)}%`}
                />
                <Line type="monotone" dataKey="iv" stroke="#7B2FBE" dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-xs text-text-muted">Insufficient IV data for skew</div>
          )}
        </div>
      </div>

      {/* Expiry selector */}
      {options.expiry_dates && options.expiry_dates.length > 0 && (
        <div className="card">
          <div className="section-title mb-2">Expiry</div>
          <div className="flex flex-wrap gap-2">
            {options.expiry_dates.slice(0, 12).map(exp => (
              <button
                key={exp}
                onClick={() => setSelectedExpiry(exp)}
                className={`px-2.5 py-1 rounded text-xs font-mono transition-all ${
                  exp === (selectedExpiry || options.selected_expiry)
                    ? 'bg-brand text-white'
                    : 'bg-bg-elevated text-text-muted hover:text-text-secondary border border-bg-border'
                }`}
              >
                {exp}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Options Chain */}
      <div className="card overflow-x-auto">
        <div className="section-title mb-3">Options Chain — {selectedExpiry || options.selected_expiry}</div>
        <table className="data-table min-w-[800px]">
          <thead>
            <tr>
              <th colSpan={4} className="text-center text-bull border-r border-bg-border">CALLS</th>
              <th className="text-center bg-bg-elevated">Strike</th>
              <th colSpan={4} className="text-center text-bear border-l border-bg-border">PUTS</th>
            </tr>
            <tr>
              <th className="text-bull">OI</th>
              <th className="text-bull">Volume</th>
              <th className="text-bull">IV</th>
              <th className="text-bull border-r border-bg-border">Price</th>
              <th className="text-center bg-bg-elevated font-bold">Strike</th>
              <th className="text-bear border-l border-bg-border">Price</th>
              <th className="text-bear">IV</th>
              <th className="text-bear">Volume</th>
              <th className="text-bear">OI</th>
            </tr>
          </thead>
          <tbody>
            {chain.map((row: OptionContract) => {
              const isATM = Math.abs(row.strike - spotPrice) < spotPrice * 0.01
              return (
                <tr key={row.strike} className={isATM ? 'bg-brand/5 border-y border-brand/20' : ''}>
                  <td className={row.in_the_money_call ? 'bg-bull-muted/30 text-bull' : 'text-text-secondary'}>
                    {(row.call_oi || 0).toLocaleString()}
                  </td>
                  <td className="text-text-muted">{(row.call_volume || 0).toLocaleString()}</td>
                  <td className="text-warn">{row.call_iv ? `${(row.call_iv * 100).toFixed(1)}%` : '—'}</td>
                  <td className="text-bull border-r border-bg-border">{fmtPrice(row.call_price)}</td>
                  <td className={`text-center font-bold bg-bg-elevated ${isATM ? 'text-brand' : 'text-text-primary'}`}>
                    {fmtPrice(row.strike)}
                  </td>
                  <td className="text-bear border-l border-bg-border">{fmtPrice(row.put_price)}</td>
                  <td className="text-warn">{row.put_iv ? `${(row.put_iv * 100).toFixed(1)}%` : '—'}</td>
                  <td className="text-text-muted">{(row.put_volume || 0).toLocaleString()}</td>
                  <td className={row.in_the_money_put ? 'bg-bear-muted/30 text-bear' : 'text-text-secondary'}>
                    {(row.put_oi || 0).toLocaleString()}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function MetricBox({ label, value, color, note }: { label: string; value: string; color?: string; note?: string }) {
  return (
    <div className="card">
      <div className="metric-label mb-1">{label}</div>
      <div className={`font-mono font-semibold ${color || 'text-text-primary'}`}>{value}</div>
      {note && <div className="text-xs text-text-muted mt-0.5">{note}</div>}
    </div>
  )
}
