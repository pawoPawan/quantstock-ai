'use client'

import { signalBadgeClass, signalColor, fmt, fmtPrice } from '@/lib/formatters'
import type { TechnicalAnalysis } from '@/types'
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip,
  ReferenceLine, BarChart, Bar, Cell,
} from 'recharts'

interface Props {
  technical: TechnicalAnalysis
  compact?: boolean
}

const INDICATOR_META: Record<string, { name: string; formula?: string }> = {
  rsi: { name: 'RSI (14)', formula: 'RSI = 100 - 100/(1+RS)' },
  macd: { name: 'MACD (12,26,9)', formula: 'MACD = EMA12 - EMA26' },
  adx: { name: 'ADX (14)', formula: 'ADX = EMA(|+DI - -DI|/(+DI + -DI))' },
  atr: { name: 'ATR (14)', formula: 'ATR = EMA(max(H-L, |H-C|, |L-C|))' },
  bollinger_bands: { name: 'Bollinger Bands (20,2σ)', formula: 'Upper/Lower = SMA20 ± 2×StdDev' },
  stochastic: { name: 'Stochastic (14,3)', formula: '%K = (C-LL14)/(HH14-LL14)×100' },
  ichimoku: { name: 'Ichimoku Cloud', formula: 'Tenkan(9), Kijun(26), Kumo' },
  supertrend: { name: 'SuperTrend (10,3)', formula: 'ST = (H+L)/2 ± 3×ATR' },
  obv: { name: 'OBV', formula: 'OBV = Cumsum(sign(ΔP)×V)' },
  cmf: { name: 'CMF (20)', formula: 'CMF = Σ(MFV)/Σ(V)' },
  mfi: { name: 'MFI (14)', formula: 'MFI = 100 - 100/(1+MFR)' },
  vwap: { name: 'VWAP', formula: 'VWAP = Σ(P×V)/Σ(V)' },
}

export default function TechnicalPanel({ technical, compact }: Props) {
  const overall = technical.overall_signal || 'neutral'
  const counts = technical.signal_counts || {}

  const indicatorRows = [
    {
      key: 'rsi',
      value: technical.rsi?.value !== undefined ? `${fmt(technical.rsi?.value)}` : '—',
      signal: technical.rsi?.signal,
      note: technical.rsi?.interpretation,
    },
    {
      key: 'macd',
      value: technical.macd?.macd !== undefined ? fmt(technical.macd?.macd, 4) : '—',
      signal: technical.macd?.trend,
      note: technical.macd?.crossover !== 'none' ? technical.macd?.crossover : undefined,
    },
    {
      key: 'adx',
      value: technical.adx?.value !== undefined ? fmt(technical.adx?.value) : '—',
      signal: technical.adx?.signal,
      note: technical.adx?.trend_strength,
    },
    {
      key: 'atr',
      value: technical.atr?.value !== undefined ? `${fmt(technical.atr?.value, 4)}` : '—',
      signal: 'neutral',
      note: technical.atr?.interpretation,
    },
    {
      key: 'bollinger_bands',
      value: technical.bollinger_bands?.pct_b !== undefined ? `%B ${fmt(technical.bollinger_bands?.pct_b, 3)}` : '—',
      signal: technical.bollinger_bands?.signal,
      note: technical.bollinger_bands?.squeeze ? '⚡ Squeeze' : undefined,
    },
    {
      key: 'stochastic',
      value: technical.stochastic?.k !== undefined ? `%K ${fmt(technical.stochastic?.k)}` : '—',
      signal: technical.stochastic?.signal,
      note: technical.stochastic?.overbought ? 'Overbought' : technical.stochastic?.oversold ? 'Oversold' : undefined,
    },
    {
      key: 'ichimoku',
      value: technical.ichimoku?.signal || '—',
      signal: technical.ichimoku?.signal,
      note: technical.ichimoku?.above_cloud ? 'Above Cloud' : 'Below/Inside Cloud',
    },
    {
      key: 'supertrend',
      value: technical.supertrend?.value !== undefined ? fmtPrice(technical.supertrend?.value) : '—',
      signal: technical.supertrend?.signal,
      note: `Dir: ${technical.supertrend?.direction === 1 ? '↑' : '↓'}`,
    },
    {
      key: 'obv',
      value: technical.obv?.value !== undefined ? (technical.obv.value / 1e6).toFixed(1) + 'M' : '—',
      signal: technical.obv?.signal,
    },
    {
      key: 'cmf',
      value: technical.cmf?.value !== undefined ? fmt(technical.cmf?.value, 4) : '—',
      signal: technical.cmf?.signal,
    },
    {
      key: 'mfi',
      value: technical.mfi?.value !== undefined ? fmt(technical.mfi?.value) : '—',
      signal: technical.mfi?.signal,
      note: technical.mfi?.overbought ? 'Overbought' : technical.mfi?.oversold ? 'Oversold' : undefined,
    },
    {
      key: 'vwap',
      value: technical.vwap?.value !== undefined ? fmtPrice(technical.vwap?.value) : '—',
      signal: technical.vwap?.signal,
    },
  ]

  const displayRows = compact ? indicatorRows.slice(0, 6) : indicatorRows

  return (
    <div className="space-y-4">
      {/* Overall signal summary */}
      <div className="card">
        <div className="flex items-center justify-between mb-3">
          <span className="section-title">Technical Analysis</span>
          <span className={`font-mono text-xs font-semibold uppercase ${signalColor(overall)}`}>
            {overall.replace('_', ' ')}
          </span>
        </div>

        {/* Signal bar */}
        <div className="flex gap-1 h-3 rounded overflow-hidden mb-2">
          <div
            className="bg-bull transition-all"
            style={{ width: `${((counts.bullish || 0) / (Object.values(counts).reduce((a, b) => a + b, 0) || 1)) * 100}%` }}
          />
          <div
            className="bg-bg-elevated"
            style={{ width: `${((counts.neutral || 0) / (Object.values(counts).reduce((a, b) => a + b, 0) || 1)) * 100}%` }}
          />
          <div
            className="bg-bear"
            style={{ width: `${((counts.bearish || 0) / (Object.values(counts).reduce((a, b) => a + b, 0) || 1)) * 100}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-text-muted font-mono">
          <span className="text-bull">{counts.bullish || 0} Bullish</span>
          <span>{counts.neutral || 0} Neutral</span>
          <span className="text-bear">{counts.bearish || 0} Bearish</span>
        </div>
      </div>

      {/* RSI mini-chart */}
      {!compact && technical.rsi?.series && technical.rsi.series.length > 0 && (
        <div className="card">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs text-text-secondary">RSI (14)</span>
            <span className={`text-xs font-mono ${technical.rsi?.value && technical.rsi.value > 70 ? 'text-bear' : technical.rsi?.value && technical.rsi.value < 30 ? 'text-bull' : 'text-text-secondary'}`}>
              {fmt(technical.rsi?.value)}
            </span>
          </div>
          <ResponsiveContainer width="100%" height={80}>
            <LineChart data={technical.rsi.series.filter(v => v !== null).map((v, i) => ({ i, v }))}>
              <XAxis dataKey="i" hide />
              <YAxis domain={[0, 100]} hide />
              <ReferenceLine y={70} stroke="#FF3D3D" strokeDasharray="3 3" strokeWidth={1} />
              <ReferenceLine y={30} stroke="#00C853" strokeDasharray="3 3" strokeWidth={1} />
              <Tooltip
                contentStyle={{ background: '#141414', border: '1px solid #242424', borderRadius: 6, fontSize: 11 }}
                formatter={(v: number) => [v?.toFixed(2), 'RSI']}
              />
              <Line type="monotone" dataKey="v" stroke="#0074D9" dot={false} strokeWidth={1.5} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Indicators table */}
      <div className="card">
        <div className="section-title mb-3">Indicator Signals</div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Indicator</th>
              <th>Value</th>
              <th>Signal</th>
              {!compact && <th>Note</th>}
            </tr>
          </thead>
          <tbody>
            {displayRows.map(({ key, value, signal, note }) => (
              <tr key={key}>
                <td className="text-text-secondary">{INDICATOR_META[key]?.name || key}</td>
                <td className="font-mono">{value}</td>
                <td>
                  <span className={signalBadgeClass(signal)}>
                    {signal?.toUpperCase() || '—'}
                  </span>
                </td>
                {!compact && <td className="text-text-muted text-xs">{note || '—'}</td>}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Support & Resistance */}
      {!compact && (technical.support_levels?.length || technical.resistance_levels?.length) ? (
        <div className="card">
          <div className="section-title mb-3">Support & Resistance</div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-xs text-bull mb-2">Support Levels</div>
              <div className="space-y-1">
                {(technical.support_levels || []).map((lvl, i) => (
                  <div key={i} className="flex justify-between text-xs font-mono">
                    <span className="text-text-muted">S{i + 1}</span>
                    <span className="text-bull">{fmtPrice(lvl)}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <div className="text-xs text-bear mb-2">Resistance Levels</div>
              <div className="space-y-1">
                {(technical.resistance_levels || []).map((lvl, i) => (
                  <div key={i} className="flex justify-between text-xs font-mono">
                    <span className="text-text-muted">R{i + 1}</span>
                    <span className="text-bear">{fmtPrice(lvl)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : null}

      {/* Volume Profile */}
      {!compact && technical.volume_profile && technical.volume_profile.length > 0 && (
        <div className="card">
          <div className="section-title mb-3">Volume Profile</div>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={technical.volume_profile} layout="vertical">
              <XAxis type="number" hide />
              <YAxis type="category" dataKey="price_level" tickFormatter={v => `$${Number(v).toFixed(0)}`} width={55} tick={{ fontSize: 10, fill: '#666' }} />
              <Tooltip
                contentStyle={{ background: '#141414', border: '1px solid #242424', borderRadius: 6, fontSize: 11 }}
                formatter={(v: number, n, p) => [p.payload.volume_pct.toFixed(1) + '%', 'Volume %']}
              />
              <Bar dataKey="volume_pct" radius={[0, 2, 2, 0]}>
                {(technical.volume_profile || []).map((entry, i) => (
                  <Cell key={i} fill={entry.volume_pct > 5 ? '#0074D9' : '#0074D940'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
