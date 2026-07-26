'use client'

import { fmt, fmtPrice, fmtPct, signColor } from '@/lib/formatters'
import type { QuantAnalysis } from '@/types'
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip,
  CartesianGrid, AreaChart, Area, ReferenceLine,
} from 'recharts'

interface Props {
  quant: QuantAnalysis
}

// ── helpers ──────────────────────────────────────────────────────────────────

function clamp(v: number, lo: number, hi: number) { return Math.max(lo, Math.min(hi, v)) }

function metricColor(score: number): string {
  if (score >= 60) return '#3fb950'
  if (score >= 35) return '#d29922'
  return '#f85149'
}

function metricBorder(score: number): string {
  if (score >= 60) return 'rgba(63,185,80,0.5)'
  if (score >= 35) return 'rgba(210,153,34,0.5)'
  return 'rgba(248,81,73,0.5)'
}

function buildCompassScore(q: QuantAnalysis): number {
  let score = 50
  const sharpe = q.sharpe_ratio ?? 0
  const calmar = q.calmar_ratio ?? 0
  const omega  = q.omega_ratio  ?? 0
  const beta   = q.beta         ?? 1
  const alpha  = q.alpha        ?? 0
  if (sharpe > 2) score += 20
  else if (sharpe > 1) score += 12
  else if (sharpe > 0.5) score += 5
  else if (sharpe < 0) score -= 15
  if (calmar > 2) score += 15
  else if (calmar > 1) score += 8
  else if (calmar < 0.3) score -= 10
  if (omega > 1.3) score += 10
  else if (omega > 1) score += 4
  else if (omega < 1) score -= 8
  if (beta > 2) score -= 10
  else if (beta > 1.5) score -= 5
  else if (beta < 0.7) score += 3
  if (alpha > 0.05) score += 12
  else if (alpha > 0) score += 4
  else if (alpha < -0.05) score -= 10
  else if (alpha < 0) score -= 4
  return clamp(Math.round(score), 0, 100)
}

function directionText(q: QuantAnalysis, score: number): { verdict: string; cls: string; body: string } {
  const beta  = q.beta  ?? 1
  const alpha = q.alpha ?? 0
  const calmar = q.calmar_ratio ?? 0
  const omega  = q.omega_ratio  ?? 0
  const r2     = q.r_squared    ?? 0

  const bullFactors: string[] = []
  const bearFactors: string[] = []
  if (calmar > 1)   bullFactors.push(`Calmar ${calmar.toFixed(2)} — recovers faster than it drawdowns`)
  if (omega > 1)    bullFactors.push(`Omega ${omega.toFixed(3)} — gains outweigh losses in aggregate`)
  if (r2 < 0.5)     bullFactors.push(`R² ${r2.toFixed(2)} — moves are mostly stock-specific, not market-driven`)
  if (alpha > 0)    bullFactors.push(`Positive Jensen α — outperforming its beta-predicted return`)
  if (beta > 1.5)   bearFactors.push(`Beta ${beta.toFixed(2)} — amplifies market drawdowns by ${beta.toFixed(1)}×`)
  if (alpha < 0)    bearFactors.push(`Alpha ${(alpha * 100).toFixed(1)}% — lagging its beta-implied expected return`)
  if ((q.sharpe_ratio ?? 0) < 0.5) bearFactors.push('Sharpe < 0.5 — risk-adjusted return is thin')

  const verdict = score >= 65 ? 'BULLISH'
    : score >= 45 ? 'CAUTIOUSLY BULLISH — MOMENTUM-DEPENDENT'
    : score >= 30 ? 'NEUTRAL — WAIT FOR CATALYST'
    : 'BEARISH'
  const cls = score >= 65 ? 'bull' : score >= 45 ? 'neutral' : score >= 30 ? 'neutral' : 'bear'

  const bStr = bullFactors.map(f => `↑ ${f}`).join('\n')
  const dStr = bearFactors.map(f => `↓ ${f}`).join('\n')
  const body = `${bStr ? bStr + '\n' : ''}${dStr ? dStr + '\n' : ''}`
    + `Net: ${score >= 65 ? 'Structure favours upside' : score >= 45 ? 'Upside bias in trending markets, exposed on macro risk-off' : 'Risk-reward is unattractive at current volatility'}.`
  return { verdict, cls, body }
}

// ── SVG Gauge ────────────────────────────────────────────────────────────────

function Gauge({ score }: { score: number }) {
  const r = 72
  const cx = 90, cy = 92
  const startAngle = -180, endAngle = 0
  const frac = score / 100
  const sweepAngle = (endAngle - startAngle) * frac + startAngle

  function polar(angleDeg: number, radius: number) {
    const a = (angleDeg * Math.PI) / 180
    return { x: cx + radius * Math.cos(a), y: cy + radius * Math.sin(a) }
  }

  function arcPath(from: number, to: number) {
    const p1 = polar(from, r)
    const p2 = polar(to, r)
    const large = (to - from) > 180 ? 1 : 0
    return `M ${p1.x} ${p1.y} A ${r} ${r} 0 ${large} 1 ${p2.x} ${p2.y}`
  }

  const needleEnd = polar(sweepAngle, r - 18)
  const col = score >= 65 ? '#3fb950' : score >= 45 ? '#d29922' : '#f85149'

  return (
    <svg viewBox="0 0 180 105" className="w-full max-w-[200px]">
      {/* Track */}
      <path d={arcPath(-180, 0)} fill="none" stroke="#21262d" strokeWidth={14} strokeLinecap="round" />
      {/* Zone colours */}
      <path d={arcPath(-180, -108)} fill="none" stroke="#f85149" strokeWidth={14} strokeLinecap="round" opacity={0.3} />
      <path d={arcPath(-108, -36)} fill="none" stroke="#d29922" strokeWidth={14} strokeLinecap="round" opacity={0.3} />
      <path d={arcPath(-36, 0)} fill="none" stroke="#3fb950" strokeWidth={14} strokeLinecap="round" opacity={0.3} />
      {/* Fill */}
      <path d={arcPath(-180, sweepAngle)} fill="none" stroke={col} strokeWidth={14} strokeLinecap="round" />
      {/* Needle */}
      <line x1={cx} y1={cy} x2={needleEnd.x} y2={needleEnd.y} stroke="#e6edf3" strokeWidth={2.5} strokeLinecap="round" />
      <circle cx={cx} cy={cy} r={4} fill="#e6edf3" />
      {/* Labels */}
      <text x={14} y={102} fontSize={9} fill="#484f58">BEAR</text>
      <text x={80} y={18} fontSize={9} fill="#484f58">MID</text>
      <text x={146} y={102} fontSize={9} fill="#484f58">BULL</text>
    </svg>
  )
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function QuantPanel({ quant }: Props) {
  const mc = quant.monte_carlo
  const drawdown = quant.drawdown_series || []
  const compassScore = buildCompassScore(quant)
  const dir = directionText(quant, compassScore)

  const drawdownData = drawdown.map((d, i) => ({ i, value: d * 100 }))
  const mcData = mc?.percentiles
    ? [
        { label: '5th', value: mc.percentiles.p5 },
        { label: '25th', value: mc.percentiles.p25 },
        { label: '50th', value: mc.percentiles.p50 },
        { label: '75th', value: mc.percentiles.p75 },
        { label: '95th', value: mc.percentiles.p95 },
      ]
    : []

  const ratios = [
    { label: 'Sharpe Ratio', value: fmt(quant.sharpe_ratio, 3), formula: '(Rp - Rf) / σp', color: (quant.sharpe_ratio ?? 0) > 1 ? 'text-bull' : (quant.sharpe_ratio ?? 0) < 0 ? 'text-bear' : 'text-warn', note: quant.sharpe_ratio && quant.sharpe_ratio > 2 ? 'Excellent' : quant.sharpe_ratio && quant.sharpe_ratio > 1 ? 'Good' : quant.sharpe_ratio && quant.sharpe_ratio > 0 ? 'Acceptable' : 'Poor' },
    { label: 'Sortino Ratio', value: fmt(quant.sortino_ratio, 3), formula: '(Rp - Rf) / σ_downside', color: (quant.sortino_ratio ?? 0) > 1 ? 'text-bull' : 'text-text-primary' },
    { label: 'Calmar Ratio', value: fmt(quant.calmar_ratio, 3), formula: 'Ann. Return / |Max Drawdown|', color: (quant.calmar_ratio ?? 0) > 1 ? 'text-bull' : 'text-text-primary' },
    { label: 'Omega Ratio', value: fmt(quant.omega_ratio, 3), formula: 'Σ gains / Σ losses (above threshold)', color: (quant.omega_ratio ?? 0) > 1 ? 'text-bull' : 'text-bear' },
    { label: 'Treynor Ratio', value: fmt(quant.treynor_ratio, 4), formula: '(Rp - Rf) / Beta', color: 'text-text-primary' },
    { label: 'Beta (vs SPY)', value: fmt(quant.beta, 3), formula: 'Cov(Rp,Rm) / Var(Rm)', color: 'text-text-primary', note: quant.beta && quant.beta > 1.5 ? 'Aggressive' : quant.beta && quant.beta < 0.5 ? 'Defensive' : 'Market-like' },
    { label: 'Alpha (Jensen)', value: quant.alpha ? fmtPct(quant.alpha * 100) : '—', formula: 'Rp - (Rf + β(Rm-Rf))', color: signColor(quant.alpha) },
    { label: 'R-Squared', value: fmt(quant.r_squared, 4), formula: 'Corr(Rp, Rm)²', color: 'text-text-primary' },
  ]

  // Metric cards with normalized scores
  const metricCards = [
    {
      label: 'Sharpe Ratio',
      raw: fmt(quant.sharpe_ratio, 3),
      score: clamp(Math.round(((quant.sharpe_ratio ?? 0) / 2) * 100), 0, 100),
      badge: (quant.sharpe_ratio ?? 0) > 1 ? 'GOOD' : (quant.sharpe_ratio ?? 0) > 0.5 ? 'ACCEPTABLE' : 'POOR',
      formula: '(Rp − Rf) / σp',
    },
    {
      label: 'Sortino Ratio',
      raw: fmt(quant.sortino_ratio, 3),
      score: clamp(Math.round(((quant.sortino_ratio ?? 0) / 2) * 100), 0, 100),
      badge: (quant.sortino_ratio ?? 0) > 1 ? 'GOOD' : 'MARGINAL',
      formula: '(Rp − Rf) / σ_downside',
    },
    {
      label: 'Calmar Ratio',
      raw: fmt(quant.calmar_ratio, 3),
      score: clamp(Math.round(((quant.calmar_ratio ?? 0) / 2) * 100), 0, 100),
      badge: (quant.calmar_ratio ?? 0) >= 1 ? 'SOLID' : 'WEAK',
      formula: 'Ann. Return / |MaxDD|',
    },
    {
      label: 'Omega Ratio',
      raw: fmt(quant.omega_ratio, 3),
      score: (quant.omega_ratio ?? 0) >= 1 ? clamp(Math.round(((quant.omega_ratio ?? 0) - 1) * 300 + 50), 50, 90) : 20,
      badge: (quant.omega_ratio ?? 0) >= 1 ? 'POSITIVE EDGE' : 'NEGATIVE EDGE',
      formula: 'Σ gains / Σ losses',
    },
    {
      label: 'Treynor Ratio',
      raw: fmt(quant.treynor_ratio, 4),
      score: clamp(Math.round(((quant.treynor_ratio ?? 0) / 0.15) * 60), 0, 100),
      badge: (quant.treynor_ratio ?? 0) > 0.1 ? 'GOOD' : 'LOW',
      formula: '(Rp − Rf) / Beta',
    },
    {
      label: 'Beta (vs SPY)',
      raw: fmt(quant.beta, 3),
      score: clamp(Math.round(100 - Math.abs((quant.beta ?? 1) - 1) * 40), 0, 100),
      badge: (quant.beta ?? 1) > 1.5 ? 'AGGRESSIVE' : (quant.beta ?? 1) < 0.7 ? 'DEFENSIVE' : 'MARKET-LIKE',
      formula: 'Cov(Rp,Rm) / Var(Rm)',
    },
    {
      label: 'Alpha (Jensen)',
      raw: quant.alpha != null ? fmtPct(quant.alpha * 100) : '—',
      score: clamp(Math.round(50 + (quant.alpha ?? 0) * 500), 0, 100),
      badge: (quant.alpha ?? 0) > 0 ? 'OUTPERFORM' : 'UNDERPERFORM',
      formula: 'Rp − (Rf + β(Rm−Rf))',
    },
    {
      label: 'R-Squared',
      raw: fmt(quant.r_squared, 4),
      score: clamp(Math.round((1 - (quant.r_squared ?? 0)) * 80 + 10), 0, 100),
      badge: (quant.r_squared ?? 0) < 0.5 ? 'IDIOSYNCRATIC' : 'MARKET-DRIVEN',
      formula: 'Corr(Rp, Rm)²',
    },
  ]

  // Bar rows for normalized chart
  const barItems = [
    { label: 'Calmar', pct: metricCards[2].score, color: metricColor(metricCards[2].score) },
    { label: 'Omega', pct: metricCards[3].score, color: metricColor(metricCards[3].score) },
    { label: 'Sortino', pct: metricCards[1].score, color: metricColor(metricCards[1].score) },
    { label: 'Sharpe', pct: metricCards[0].score, color: metricColor(metricCards[0].score) },
    { label: 'Treynor', pct: metricCards[4].score, color: metricColor(metricCards[4].score) },
    { label: 'Alpha', pct: metricCards[6].score, color: metricColor(metricCards[6].score) },
  ]

  return (
    <div className="space-y-4">

      {/* ── Direction Compass ── */}
      <div className="card">
        <div className="section-title mb-4">Quant Direction Compass</div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

          {/* Gauge + bar chart */}
          <div className="flex flex-col gap-4">
            <div className="flex flex-col items-center gap-1">
              <Gauge score={compassScore} />
              <div style={{ color: metricColor(compassScore) }} className="text-3xl font-bold font-mono">
                {compassScore}
              </div>
              <div className="text-xs text-text-muted tracking-widest uppercase">Composite Quant Score</div>
            </div>

            <div className="space-y-2">
              {barItems.map(b => (
                <div key={b.label} className="flex items-center gap-2 text-xs">
                  <span className="w-14 text-text-muted shrink-0">{b.label}</span>
                  <div className="flex-1 h-1.5 bg-bg-elevated rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{ width: `${b.pct}%`, background: b.color }}
                    />
                  </div>
                  <span className="w-8 text-right font-mono shrink-0" style={{ color: b.color }}>
                    {b.pct}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Signal pills + direction text */}
          <div className="flex flex-col gap-3">
            <div className="grid grid-cols-2 gap-2">
              {metricCards.map(m => (
                <div
                  key={m.label}
                  className="rounded-lg p-2.5 text-xs"
                  style={{
                    background: 'var(--bg-elevated)',
                    border: `1px solid ${metricBorder(m.score)}`,
                  }}
                >
                  <div className="flex items-center gap-1.5 mb-1">
                    <div className="w-2 h-2 rounded-full shrink-0" style={{ background: metricColor(m.score) }} />
                    <span className="text-text-muted">{m.label}</span>
                  </div>
                  <div className="font-mono font-bold text-sm" style={{ color: metricColor(m.score) }}>
                    {m.raw}
                  </div>
                  <div className="text-text-muted" style={{ fontSize: 9, marginTop: 2 }}>{m.badge}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Direction verdict */}
        <div className="mt-4 rounded-lg p-4 text-xs leading-relaxed space-y-2"
          style={{ background: 'var(--bg-elevated)', border: '1px solid var(--bg-border)' }}>
          <div className={`inline-flex items-center gap-2 font-bold text-sm px-3 py-1 rounded-md mb-2 ${
            dir.cls === 'bull' ? 'bg-bull/10 text-bull border border-bull/30'
            : dir.cls === 'bear' ? 'bg-bear/10 text-bear border border-bear/30'
            : 'bg-warn/10 text-warn border border-warn/30'
          }`}>
            {dir.cls === 'bull' ? '▲' : dir.cls === 'bear' ? '▼' : '⚡'} {dir.verdict}
          </div>
          {dir.body.split('\n').filter(Boolean).map((line, i) => (
            <p key={i} className="text-text-secondary">{line}</p>
          ))}
        </div>
      </div>

      {/* ── Returns & Volatility header ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="card">
          <div className="metric-label">Annualized Return</div>
          <div className={`font-mono font-bold text-xl ${signColor(quant.annualized_return)}`}>
            {fmtPct(quant.annualized_return_pct)}
          </div>
        </div>
        <div className="card">
          <div className="metric-label">Annualized Volatility</div>
          <div className="font-mono font-bold text-xl text-warn">{fmtPct(quant.annualized_volatility_pct)}</div>
        </div>
        <div className="card">
          <div className="metric-label">Max Drawdown</div>
          <div className="font-mono font-bold text-xl text-bear">{fmtPct(quant.max_drawdown_pct)}</div>
          {quant.max_drawdown_duration && (
            <div className="text-xs text-text-muted">{quant.max_drawdown_duration} days</div>
          )}
        </div>
        <div className="card">
          <div className="metric-label">CAPM Expected Return</div>
          <div className={`font-mono font-bold text-xl ${signColor(quant.capm_expected_return)}`}>
            {quant.capm_expected_return ? fmtPct(quant.capm_expected_return * 100) : '—'}
          </div>
        </div>
      </div>

      {/* ── Risk metrics ── */}
      <div className="grid grid-cols-3 gap-3">
        <div className="card">
          <div className="metric-label">1-Day VaR (95%)</div>
          <div className="font-mono font-bold text-bear">{quant.var_95_1d ? `-$${Math.abs(quant.var_95_1d).toFixed(2)}` : '—'}</div>
          <div className="text-xs text-text-muted">Loss not exceeded 95% of days</div>
        </div>
        <div className="card">
          <div className="metric-label">1-Day VaR (99%)</div>
          <div className="font-mono font-bold text-bear">{quant.var_99_1d ? `-$${Math.abs(quant.var_99_1d).toFixed(2)}` : '—'}</div>
          <div className="text-xs text-text-muted">Loss not exceeded 99% of days</div>
        </div>
        <div className="card">
          <div className="metric-label">CVaR (95%)</div>
          <div className="font-mono font-bold text-bear">{quant.cvar_95_1d ? `-$${Math.abs(quant.cvar_95_1d).toFixed(2)}` : '—'}</div>
          <div className="text-xs text-text-muted">Expected loss beyond VaR</div>
        </div>
      </div>

      {/* ── Risk-adjusted ratios table ── */}
      <div className="card">
        <div className="section-title mb-3">Risk-Adjusted Performance Ratios</div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Metric</th>
              <th>Value</th>
              <th>Assessment</th>
              <th>Formula</th>
            </tr>
          </thead>
          <tbody>
            {ratios.map(r => (
              <tr key={r.label}>
                <td className="text-text-secondary">{r.label}</td>
                <td className={`font-mono font-semibold ${r.color}`}>{r.value}</td>
                <td className="text-text-muted">{r.note || '—'}</td>
                <td className="text-text-muted text-xs font-mono">{r.formula}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ── Drawdown chart ── */}
      {drawdownData.length > 0 && (
        <div className="card">
          <div className="section-title mb-2">Drawdown History</div>
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={drawdownData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" />
              <XAxis dataKey="i" hide />
              <YAxis tickFormatter={v => `${v?.toFixed(0)}%`} tick={{ fontSize: 10, fill: '#666' }} />
              <Tooltip
                contentStyle={{ background: '#141414', border: '1px solid #242424', borderRadius: 6, fontSize: 11 }}
                formatter={(v: number) => [`${v?.toFixed(2)}%`, 'Drawdown']}
              />
              <ReferenceLine y={0} stroke="#444" />
              <Area type="monotone" dataKey="value" stroke="#FF3D3D" fill="#FF3D3D20" strokeWidth={1.5} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* ── Monte Carlo ── */}
      {mc?.simulations != null && (
        <div className="card">
          <div className="section-title mb-3">Monte Carlo Simulation — {mc.simulations.toLocaleString()} paths, 1-year horizon</div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div>
              <div className="metric-label">Mean Price</div>
              <div className="font-mono font-bold text-text-primary">{fmtPrice(mc.mean_price)}</div>
            </div>
            <div>
              <div className="metric-label">Expected Return</div>
              <div className={`font-mono font-bold ${mc.expected_return_pct > 0 ? 'text-bull' : 'text-bear'}`}>
                {mc.expected_return_pct > 0 ? '+' : ''}{mc.expected_return_pct.toFixed(1)}%
              </div>
            </div>
            <div>
              <div className="metric-label">Prob. Profit</div>
              <div className="font-mono font-bold text-text-primary">{(mc.probability_profit * 100).toFixed(1)}%</div>
            </div>
            <div>
              <div className="metric-label">VaR 95% (1Y)</div>
              <div className="font-mono font-bold text-bear">{fmtPrice(mc.var_95)}</div>
            </div>
          </div>

          <div className="grid grid-cols-5 gap-2 mb-4">
            {mcData.map(p => (
              <div key={p.label} className="text-center">
                <div className="text-xs text-text-muted">{p.label}</div>
                <div className="font-mono text-xs text-text-primary">{fmtPrice(p.value)}</div>
              </div>
            ))}
          </div>

          {mc.sample_paths && mc.sample_paths.length > 0 && (
            <ResponsiveContainer width="100%" height={180}>
              <LineChart>
                <CartesianGrid strokeDasharray="3 3" stroke="#111" />
                <XAxis type="number" dataKey="i" domain={[0, mc.sample_paths[0]?.length - 1]} tick={{ fontSize: 9, fill: '#666' }} tickCount={5} tickFormatter={v => `D${v}`} />
                <YAxis tick={{ fontSize: 9, fill: '#666' }} tickFormatter={v => `$${v?.toFixed(0)}`} domain={['auto', 'auto']} />
                <Tooltip
                  contentStyle={{ background: '#141414', border: '1px solid #242424', borderRadius: 6, fontSize: 11 }}
                  formatter={(v: number) => [`$${v?.toFixed(2)}`]}
                />
                {mc.sample_paths.slice(0, 30).map((path, pi) => (
                  <Line
                    key={pi}
                    type="monotone"
                    data={path.map((v, i) => ({ i, v }))}
                    dataKey="v"
                    stroke={path[path.length - 1] >= mc.current_price ? '#00C85320' : '#FF3D3D20'}
                    dot={false}
                    strokeWidth={0.8}
                    isAnimationActive={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      )}

      {/* ── Kelly Criterion ── */}
      {quant.kelly_criterion?.kelly_pct != null && (
        <div className="card">
          <div className="section-title mb-3">Kelly Criterion — Optimal Position Sizing</div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="metric-label">Full Kelly</div>
              <div className="font-mono font-bold text-text-primary">{quant.kelly_criterion.kelly_pct.toFixed(1)}%</div>
            </div>
            <div>
              <div className="metric-label">Half Kelly (Recommended)</div>
              <div className="font-mono font-bold text-brand">{quant.kelly_criterion.half_kelly_pct.toFixed(1)}%</div>
            </div>
            <div>
              <div className="metric-label">Win Rate</div>
              <div className="font-mono">{(quant.kelly_criterion.win_rate * 100).toFixed(1)}%</div>
            </div>
            <div>
              <div className="metric-label">Win/Loss Ratio</div>
              <div className="font-mono">{quant.kelly_criterion.avg_win_loss_ratio.toFixed(2)}x</div>
            </div>
          </div>
          <div className="text-xs text-text-muted mt-3">{quant.kelly_criterion.interpretation}</div>
          <div className="text-xs text-text-muted mt-1">Formula: f* = (p·b - q) / b where p = win rate, b = avg win/loss ratio</div>
        </div>
      )}
    </div>
  )
}
