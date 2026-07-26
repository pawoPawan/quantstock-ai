'use client'

import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { createChart, ColorType, CrosshairMode, LineStyle, CandlestickSeries, HistogramSeries, LineSeries } from 'lightweight-charts'
import { stockApi } from '@/lib/api'
import type { HistoricalData } from '@/types'

const PERIODS = ['1D', '5D', '1M', '3M', '6M', '1Y', '5Y', 'MAX'] as const
type Period = typeof PERIODS[number]

const CHART_TYPES = ['Candles', 'Line'] as const
type ChartType = typeof CHART_TYPES[number]

const INDICATORS = ['MA20', 'EMA50', 'VWAP', 'BB'] as const
type Indicator = typeof INDICATORS[number]

interface Props {
  ticker: string
  history?: HistoricalData
}

export default function PriceChart({ ticker, history: initialHistory }: Props) {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<ReturnType<typeof createChart> | null>(null)
  const [period, setPeriod] = useState<Period>('1Y')
  const [chartType, setChartType] = useState<ChartType>('Candles')
  const [indicators, setIndicators] = useState<Set<Indicator>>(new Set(['MA20']))

  const { data: history } = useQuery({
    queryKey: ['history', ticker, period],
    queryFn: () => stockApi.getHistory(ticker, period),
    initialData: period === '1Y' ? initialHistory : undefined,
    staleTime: 60_000,
  })

  useEffect(() => {
    if (!chartRef.current || !history?.bars?.length) return

    // Clean up
    if (chartInstance.current) {
      chartInstance.current.remove()
    }

    const chart = createChart(chartRef.current, {
      width: chartRef.current.clientWidth,
      height: 400,
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#666666',
        fontSize: 11,
        fontFamily: "'JetBrains Mono', monospace",
      },
      grid: {
        vertLines: { color: 'rgba(255,255,255,0.03)', style: LineStyle.Dotted },
        horzLines: { color: 'rgba(255,255,255,0.03)', style: LineStyle.Dotted },
      },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: '#242424' },
      timeScale: { borderColor: '#242424', timeVisible: true },
    })
    chartInstance.current = chart

    const bars = Array.from(
      history.bars.reduce((map, b) => {
        map.set(b.timestamp.slice(0, 10), b)
        return map
      }, new Map<string, (typeof history.bars)[0]>()).values()
    ).sort((a, b) => a.timestamp.localeCompare(b.timestamp))

    // ── Main series ──────────────────────────────────────────────────────────
    if (chartType === 'Candles') {
      const candleSeries = chart.addSeries(CandlestickSeries, {
        upColor: '#00C853',
        downColor: '#FF3D3D',
        borderUpColor: '#00C853',
        borderDownColor: '#FF3D3D',
        wickUpColor: '#00C853',
        wickDownColor: '#FF3D3D',
      })
      candleSeries.setData(bars.map(b => ({
        time: b.timestamp.slice(0, 10) as any,
        open: b.open, high: b.high, low: b.low, close: b.close,
      })))
    } else {
      const lineSeries = chart.addSeries(LineSeries, {
        color: '#0074D9',
        lineWidth: 2,
      })
      lineSeries.setData(bars.map(b => ({ time: b.timestamp.slice(0, 10) as any, value: b.close })))
    }

    // ── Volume ────────────────────────────────────────────────────────────────
    const volSeries = chart.addSeries(HistogramSeries, {
      color: '#0074D930',
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    })
    chart.priceScale('volume').applyOptions({ scaleMargins: { top: 0.85, bottom: 0 } })
    volSeries.setData(bars.map(b => ({
      time: b.timestamp.slice(0, 10) as any,
      value: b.volume,
      color: b.close >= b.open ? '#00C85330' : '#FF3D3D30',
    })))

    // ── MA20 ─────────────────────────────────────────────────────────────────
    if (indicators.has('MA20')) {
      const closes = bars.map(b => b.close)
      const ma20 = closes.map((_, i) => {
        if (i < 19) return null
        const slice = closes.slice(i - 19, i + 1)
        return slice.reduce((a, b) => a + b, 0) / 20
      })
      const ma20Series = chart.addSeries(LineSeries, { color: '#FFB800', lineWidth: 1, title: 'MA20' })
      ma20Series.setData(bars.map((b, i) => ma20[i] !== null
        ? { time: b.timestamp.slice(0, 10) as any, value: ma20[i]! }
        : { time: b.timestamp.slice(0, 10) as any, value: NaN }
      ).filter(d => !isNaN(d.value)))
    }

    // ── EMA50 ────────────────────────────────────────────────────────────────
    if (indicators.has('EMA50')) {
      const closes = bars.map(b => b.close)
      const k = 2 / (50 + 1)
      const ema50: number[] = []
      closes.forEach((c, i) => {
        if (i === 0) { ema50.push(c); return }
        ema50.push(c * k + ema50[i - 1] * (1 - k))
      })
      const ema50Series = chart.addSeries(LineSeries, { color: '#7B2FBE', lineWidth: 1, title: 'EMA50' })
      ema50Series.setData(bars.slice(49).map((b, i) => ({ time: b.timestamp.slice(0, 10) as any, value: ema50[i + 49] })))
    }

    // Fit content
    chart.timeScale().fitContent()

    // Resize observer
    const observer = new ResizeObserver(() => {
      if (chartRef.current) chart.applyOptions({ width: chartRef.current.clientWidth })
    })
    if (chartRef.current) observer.observe(chartRef.current)

    return () => {
      observer.disconnect()
      chart.remove()
      chartInstance.current = null
    }
  }, [history, chartType, indicators])

  const toggleIndicator = (ind: Indicator) => {
    setIndicators(prev => {
      const next = new Set(prev)
      next.has(ind) ? next.delete(ind) : next.add(ind)
      return next
    })
  }

  return (
    <div>
      {/* Toolbar */}
      <div className="flex items-center justify-between gap-4 mb-3 flex-wrap">
        {/* Period */}
        <div className="flex gap-1">
          {PERIODS.map(p => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-2.5 py-1 text-xs font-mono rounded transition-all ${
                period === p ? 'bg-brand text-white' : 'text-text-muted hover:text-text-secondary hover:bg-bg-elevated'
              }`}
            >
              {p}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-3">
          {/* Chart type */}
          <div className="flex gap-1">
            {CHART_TYPES.map(ct => (
              <button
                key={ct}
                onClick={() => setChartType(ct)}
                className={`px-2.5 py-1 text-xs font-mono rounded border transition-all ${
                  chartType === ct ? 'border-brand/40 bg-brand/10 text-brand' : 'border-bg-border text-text-muted hover:border-bg-hover'
                }`}
              >
                {ct}
              </button>
            ))}
          </div>

          {/* Indicators */}
          <div className="flex gap-1">
            {INDICATORS.map(ind => (
              <button
                key={ind}
                onClick={() => toggleIndicator(ind)}
                className={`px-2 py-1 text-xs font-mono rounded border transition-all ${
                  indicators.has(ind) ? 'border-warn/40 bg-warn/10 text-warn' : 'border-bg-border text-text-muted hover:border-bg-hover'
                }`}
              >
                {ind}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Chart */}
      <div ref={chartRef} className="w-full rounded-lg overflow-hidden tv-chart-container" />
    </div>
  )
}
