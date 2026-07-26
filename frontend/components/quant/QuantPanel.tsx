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

export default function QuantPanel({ quant }: Props) {
  const mc = quant.monte_carlo
  const drawdown = quant.drawdown_series || []

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

  return (
    <div className="space-y-4">
      {/* Returns & Volatility header */}
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

      {/* Risk metrics */}
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

      {/* Risk-adjusted ratios */}
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

      {/* Drawdown chart */}
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

      {/* Monte Carlo */}
      {mc && (
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

          {/* Sample MC paths */}
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

      {/* Kelly Criterion */}
      {quant.kelly_criterion && (
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
