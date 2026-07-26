/**
 * Formatting utilities for financial data display.
 */

export function fmt(value: number | null | undefined, decimals = 2): string {
  if (value === null || value === undefined || isNaN(value)) return '—'
  return value.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
}

export function fmtPrice(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) return '—'
  return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 4 })}`
}

export function fmtPct(value: number | null | undefined, decimals = 2): string {
  if (value === null || value === undefined || isNaN(value)) return '—'
  return `${value >= 0 ? '+' : ''}${value.toFixed(decimals)}%`
}

export function fmtPctRaw(value: number | null | undefined, decimals = 2): string {
  if (value === null || value === undefined || isNaN(value)) return '—'
  const pct = value * 100
  return `${pct >= 0 ? '+' : ''}${pct.toFixed(decimals)}%`
}

export function fmtChange(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) return '—'
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}`
}

export function fmtMarketCap(value: number | null | undefined): string {
  if (!value) return '—'
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`
  return `$${value.toLocaleString()}`
}

export function fmtVolume(value: number | null | undefined): string {
  if (!value) return '—'
  if (value >= 1e9) return `${(value / 1e9).toFixed(2)}B`
  if (value >= 1e6) return `${(value / 1e6).toFixed(2)}M`
  if (value >= 1e3) return `${(value / 1e3).toFixed(2)}K`
  return value.toString()
}

export function fmtMultiple(value: number | null | undefined, suffix = 'x'): string {
  if (value === null || value === undefined || isNaN(value)) return '—'
  return `${value.toFixed(2)}${suffix}`
}

export function fmtGreek(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) return '—'
  return value.toFixed(4)
}

export function fmtHigherGreek(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) return '—'
  return value.toExponential(3)
}

export function signColor(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) return 'text-text-secondary'
  return value >= 0 ? 'text-bull' : 'text-bear'
}

export function signBg(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) return ''
  return value >= 0 ? 'bg-bull-muted text-bull' : 'bg-bear-muted text-bear'
}

export function signalColor(signal: string | undefined): string {
  if (!signal) return 'text-text-secondary'
  if (signal.includes('bull')) return 'text-bull'
  if (signal.includes('bear')) return 'text-bear'
  return 'text-warn'
}

export function signalBadgeClass(signal: string | undefined): string {
  if (!signal) return 'badge-neutral'
  if (signal.includes('bull')) return 'badge-bull'
  if (signal.includes('bear')) return 'badge-bear'
  return 'badge-neutral'
}

export function gradeColor(grade: string | undefined): string {
  if (!grade) return 'text-text-secondary'
  if (grade.startsWith('A')) return 'text-bull'
  if (grade.startsWith('B')) return 'text-brand'
  if (grade.startsWith('C')) return 'text-warn'
  return 'text-bear'
}

export function scoreColor(score: number): string {
  if (score >= 70) return '#00C853'
  if (score >= 55) return '#0074D9'
  if (score >= 40) return '#FFB800'
  return '#FF3D3D'
}

export function recommendationColor(rec: string | undefined): string {
  if (!rec) return 'text-text-secondary'
  if (rec === 'Strong Buy') return 'text-bull'
  if (rec === 'Buy') return 'text-[#69F0AE]'
  if (rec === 'Hold') return 'text-warn'
  if (rec === 'Sell') return 'text-[#FF7979]'
  if (rec === 'Strong Sell') return 'text-bear'
  return 'text-text-secondary'
}
