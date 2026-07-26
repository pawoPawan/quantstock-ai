'use client'

import { fmtPrice, fmtPctRaw, fmtMarketCap, fmtMultiple, fmtVolume, signColor } from '@/lib/formatters'
import type { StockInfo } from '@/types'

interface MetricCardProps {
  label: string
  value: string
  sub?: string
  color?: string
}

function MetricCard({ label, value, sub, color }: MetricCardProps) {
  return (
    <div className="bg-bg-card border border-bg-border rounded-lg p-3">
      <div className="metric-label mb-1">{label}</div>
      <div className={`font-mono font-semibold text-sm ${color || 'text-text-primary'}`}>{value}</div>
      {sub && <div className="text-xs text-text-muted mt-0.5 font-mono">{sub}</div>}
    </div>
  )
}

export default function MetricsGrid({ info }: { info: StockInfo }) {
  const metrics: MetricCardProps[] = [
    { label: 'P/E Ratio', value: fmtMultiple(info.pe_ratio), sub: `Fwd: ${fmtMultiple(info.forward_pe)}` },
    { label: 'PEG Ratio', value: fmtMultiple(info.peg_ratio), sub: info.peg_ratio && info.peg_ratio < 1 ? 'Undervalued' : info.peg_ratio && info.peg_ratio > 2 ? 'Premium' : 'Fair' },
    { label: 'P/B Ratio', value: fmtMultiple(info.price_to_book) },
    { label: 'EPS (TTM)', value: info.eps ? `$${info.eps.toFixed(2)}` : '—', sub: `Fwd: $${info.eps_forward?.toFixed(2) ?? '—'}` },
    { label: 'Market Cap', value: fmtMarketCap(info.market_cap) },
    { label: 'Enterprise Value', value: fmtMarketCap(info.enterprise_value) },
    { label: 'Volume', value: fmtVolume(info.volume), sub: `Avg: ${fmtVolume(info.avg_volume)}` },
    { label: 'Beta', value: info.beta?.toFixed(2) ?? '—', sub: info.beta && info.beta > 1.5 ? 'High volatility' : info.beta && info.beta < 0.5 ? 'Defensive' : 'Market-like' },
    { label: 'Dividend Yield', value: info.dividend_yield ? fmtPctRaw(info.dividend_yield) : 'None', sub: info.dividend_rate ? `$${info.dividend_rate.toFixed(2)}/yr` : undefined },
    { label: 'ROE', value: fmtPctRaw(info.roe), color: signColor(info.roe) },
    { label: 'ROA', value: fmtPctRaw(info.roa), color: signColor(info.roa) },
    { label: 'Operating Margin', value: fmtPctRaw(info.operating_margin), color: signColor(info.operating_margin) },
    { label: 'Net Margin', value: fmtPctRaw(info.profit_margin), color: signColor(info.profit_margin) },
    { label: 'Revenue Growth', value: fmtPctRaw(info.revenue_growth), color: signColor(info.revenue_growth) },
    { label: 'Free Cash Flow', value: fmtMarketCap(info.free_cashflow), color: (info.free_cashflow ?? 0) > 0 ? 'text-bull' : 'text-bear' },
    { label: 'Debt/Equity', value: fmtMultiple(info.debt_to_equity), color: (info.debt_to_equity ?? 0) > 2 ? 'text-bear' : (info.debt_to_equity ?? 0) < 0.5 ? 'text-bull' : 'text-text-primary' },
    { label: 'Current Ratio', value: fmtMultiple(info.current_ratio), color: (info.current_ratio ?? 0) > 2 ? 'text-bull' : (info.current_ratio ?? 0) < 1 ? 'text-bear' : 'text-text-primary' },
    { label: 'Short Interest', value: info.short_percent ? fmtPctRaw(info.short_percent) : '—', color: (info.short_percent ?? 0) > 0.15 ? 'text-bear' : 'text-text-primary' },
  ]

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2 mt-4">
      {metrics.map((m) => (
        <MetricCard key={m.label} {...m} />
      ))}
    </div>
  )
}
