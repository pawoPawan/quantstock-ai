'use client'

import { fmtPrice, fmtMarketCap, fmtPct, signColor, fmt } from '@/lib/formatters'
import type { FundamentalAnalysis, StockInfo } from '@/types'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, LineChart, Line, CartesianGrid,
} from 'recharts'

interface Props {
  fundamental: FundamentalAnalysis
  info: StockInfo
}

export default function FundamentalPanel({ fundamental, info }: Props) {
  const { income_statements, balance_sheets, cash_flows, dcf } = fundamental

  // Prepare chart data
  const revenueData = income_statements.slice().reverse().map(s => ({
    year: s.year?.slice(0, 7),
    revenue: s.revenue ? s.revenue / 1e9 : null,
    net_income: s.net_income ? s.net_income / 1e9 : null,
    ebitda: s.ebitda ? s.ebitda / 1e9 : null,
  }))

  const marginData = income_statements.slice().reverse().map(s => ({
    year: s.year?.slice(0, 7),
    gross: s.gross_margin,
    operating: s.operating_margin,
    net: s.net_margin,
  }))

  const fcfData = cash_flows.slice().reverse().map(s => ({
    year: s.year?.slice(0, 7),
    ocf: s.operating_cash_flow ? s.operating_cash_flow / 1e9 : null,
    fcf: s.free_cash_flow ? s.free_cash_flow / 1e9 : null,
    capex: s.capex ? Math.abs(s.capex) / 1e9 : null,
  }))

  return (
    <div className="space-y-4">
      {/* Key ratios */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <RatioCard label="ROE" value={fmtPct(fundamental.roe ? fundamental.roe * 100 : null)} color={signColor(fundamental.roe)} />
        <RatioCard label="ROA" value={fmtPct(fundamental.roa ? fundamental.roa * 100 : null)} color={signColor(fundamental.roa)} />
        <RatioCard label="ROCE" value={fmtPct(fundamental.roce ? fundamental.roce * 100 : null)} color={signColor(fundamental.roce)} />
        <RatioCard label="Net Margin" value={fmtPct(fundamental.net_margin ? fundamental.net_margin * 100 : null)} color={signColor(fundamental.net_margin)} />
        <RatioCard label="Revenue CAGR 3Y" value={fundamental.revenue_cagr_3y ? fmtPct(fundamental.revenue_cagr_3y * 100) : '—'} color={signColor(fundamental.revenue_cagr_3y)} />
        <RatioCard label="EPS CAGR 3Y" value={fundamental.eps_cagr_3y ? fmtPct(fundamental.eps_cagr_3y * 100) : '—'} color={signColor(fundamental.eps_cagr_3y)} />
        <RatioCard label="Debt/Equity" value={fundamental.debt_to_equity ? fmt(fundamental.debt_to_equity) + 'x' : '—'} color={(fundamental.debt_to_equity ?? 0) > 2 ? 'text-bear' : (fundamental.debt_to_equity ?? 0) < 0.5 ? 'text-bull' : 'text-text-primary'} />
        <RatioCard label="Current Ratio" value={fundamental.current_ratio ? fmt(fundamental.current_ratio) + 'x' : '—'} color={(fundamental.current_ratio ?? 0) >= 2 ? 'text-bull' : (fundamental.current_ratio ?? 0) < 1 ? 'text-bear' : 'text-text-primary'} />
      </div>

      {/* Revenue & Income chart */}
      {revenueData.length > 0 && (
        <div className="card">
          <div className="section-title mb-3">Revenue & Profitability ($B)</div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={revenueData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" />
              <XAxis dataKey="year" tick={{ fontSize: 10, fill: '#666' }} />
              <YAxis tick={{ fontSize: 10, fill: '#666' }} tickFormatter={v => `$${v}B`} />
              <Tooltip
                contentStyle={{ background: '#141414', border: '1px solid #242424', borderRadius: 6, fontSize: 11 }}
                formatter={(v: number) => [`$${v?.toFixed(2)}B`]}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="revenue" name="Revenue" fill="#0074D9" radius={[3, 3, 0, 0]} />
              <Bar dataKey="net_income" name="Net Income" fill="#00C853" radius={[3, 3, 0, 0]} />
              <Bar dataKey="ebitda" name="EBITDA" fill="#FFB80060" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Margin trends */}
      {marginData.length > 0 && (
        <div className="card">
          <div className="section-title mb-3">Margin Trends (%)</div>
          <ResponsiveContainer width="100%" height={160}>
            <LineChart data={marginData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" />
              <XAxis dataKey="year" tick={{ fontSize: 10, fill: '#666' }} />
              <YAxis tick={{ fontSize: 10, fill: '#666' }} tickFormatter={v => `${v?.toFixed(0)}%`} />
              <Tooltip
                contentStyle={{ background: '#141414', border: '1px solid #242424', borderRadius: 6, fontSize: 11 }}
                formatter={(v: number) => [`${v?.toFixed(1)}%`]}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line type="monotone" dataKey="gross" name="Gross Margin" stroke="#0074D9" dot={false} strokeWidth={2} />
              <Line type="monotone" dataKey="operating" name="Op. Margin" stroke="#FFB800" dot={false} strokeWidth={2} />
              <Line type="monotone" dataKey="net" name="Net Margin" stroke="#00C853" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Cash Flow */}
      {fcfData.length > 0 && (
        <div className="card">
          <div className="section-title mb-3">Cash Flow ($B)</div>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={fcfData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" />
              <XAxis dataKey="year" tick={{ fontSize: 10, fill: '#666' }} />
              <YAxis tick={{ fontSize: 10, fill: '#666' }} tickFormatter={v => `$${v}B`} />
              <Tooltip
                contentStyle={{ background: '#141414', border: '1px solid #242424', borderRadius: 6, fontSize: 11 }}
                formatter={(v: number) => [`$${v?.toFixed(2)}B`]}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="ocf" name="Operating CF" fill="#0074D9" radius={[3, 3, 0, 0]} />
              <Bar dataKey="fcf" name="Free CF" fill="#00C853" radius={[3, 3, 0, 0]} />
              <Bar dataKey="capex" name="Capex" fill="#FF3D3D60" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* DCF Valuation */}
      {dcf && (
        <div className="card">
          <div className="section-title mb-3">DCF Valuation</div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div>
              <div className="metric-label">Intrinsic Value</div>
              <div className="font-mono font-bold text-lg text-text-primary">{fmtPrice(dcf.intrinsic_value)}</div>
            </div>
            <div>
              <div className="metric-label">Current Price</div>
              <div className="font-mono font-bold text-lg text-text-primary">{fmtPrice(dcf.current_price)}</div>
            </div>
            <div>
              <div className="metric-label">Upside / Downside</div>
              <div className={`font-mono font-bold text-lg ${dcf.upside_pct > 0 ? 'text-bull' : 'text-bear'}`}>
                {dcf.upside_pct > 0 ? '+' : ''}{dcf.upside_pct.toFixed(1)}%
              </div>
            </div>
            <div>
              <div className="metric-label">Margin of Safety</div>
              <div className={`font-mono font-bold text-lg ${dcf.margin_of_safety > 0 ? 'text-bull' : 'text-bear'}`}>
                {(dcf.margin_of_safety * 100).toFixed(1)}%
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
            <div className="flex justify-between"><span className="text-text-muted">WACC</span><span className="font-mono">{(dcf.wacc * 100).toFixed(1)}%</span></div>
            <div className="flex justify-between"><span className="text-text-muted">Terminal Growth</span><span className="font-mono">{(dcf.terminal_growth_rate * 100).toFixed(1)}%</span></div>
            <div className="flex justify-between"><span className="text-text-muted">Stage 1 PV</span><span className="font-mono">{fmtMarketCap(dcf.stage1_value)}</span></div>
            <div className="flex justify-between"><span className="text-text-muted">Terminal Value %</span><span className="font-mono">{dcf.tv_pct_of_ev?.toFixed(1)}%</span></div>
          </div>

          {/* DCF waterfall */}
          <div className="text-xs text-text-muted">
            Assumptions: {dcf.assumptions.growth_1_5yr}% growth (Y1-5) → {dcf.assumptions.growth_6_10yr}% (Y6-10) → {dcf.assumptions.terminal_growth_pct}% terminal.
            WACC {dcf.assumptions.wacc_pct}%.
          </div>
        </div>
      )}

      {/* Income Statement table */}
      {income_statements.length > 0 && (
        <div className="card overflow-x-auto">
          <div className="section-title mb-3">Income Statement</div>
          <table className="data-table min-w-[600px]">
            <thead>
              <tr>
                <th>Period</th>
                <th>Revenue</th>
                <th>Gross Profit</th>
                <th>EBITDA</th>
                <th>Net Income</th>
                <th>EPS</th>
                <th>Net Margin</th>
              </tr>
            </thead>
            <tbody>
              {income_statements.map((stmt) => (
                <tr key={stmt.year}>
                  <td className="text-text-secondary">{stmt.year?.slice(0, 7)}</td>
                  <td>{fmtMarketCap(stmt.revenue)}</td>
                  <td>{fmtMarketCap(stmt.gross_profit)}</td>
                  <td>{fmtMarketCap(stmt.ebitda)}</td>
                  <td className={signColor(stmt.net_income)}>{fmtMarketCap(stmt.net_income)}</td>
                  <td className={signColor(stmt.eps)}>{stmt.eps ? `$${stmt.eps.toFixed(2)}` : '—'}</td>
                  <td className={signColor(stmt.net_margin)}>{stmt.net_margin ? `${stmt.net_margin.toFixed(1)}%` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function RatioCard({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="card">
      <div className="metric-label mb-1">{label}</div>
      <div className={`font-mono font-semibold ${color || 'text-text-primary'}`}>{value}</div>
    </div>
  )
}
