import { useMemo, useRef } from 'react'

// ─── Types ────────────────────────────────────────────────────────────────────
interface ChartPoint {
  price?: number
  value?: number
  open?: number
  high?: number
  low?: number
  close?: number
  time?: string | number
}

interface Candle {
  open: number
  high: number
  low: number
  close: number
}

interface CandleChartProps {
  data: ChartPoint[]
  candles?: number
  height?: number
}

// ─── Seeded pseudo-random ─────────────────────────────────────────────────────
// Takes an explicit seed so each session produces a unique but stable chart.
function seededRand(seed: number, index: number): number {
  const x = Math.sin(seed + index + 1) * 43758.5453123
  return x - Math.floor(x)
}

// ─── Build OHLC candles from scalar price array ───────────────────────────────
function buildCandles(data: ChartPoint[], count: number, sessionSeed: number): Candle[] {
  if (!data || data.length === 0) return []

  // Already has OHLC — use directly
  if (data[0].open !== undefined) {
    return data.slice(-count).map(d => ({
      open:  d.open!,
      high:  d.high!,
      low:   d.low!,
      close: d.close!,
    }))
  }

  const prices = data.map(d => d.price ?? d.value ?? 0)
  const len = prices.length

  return Array.from({ length: count }, (_, i) => {
    // Map candle index to position in prices array
    const startFrac = i / count
    const endFrac   = (i + 1) / count
    const startIdx  = Math.round(startFrac * (len - 1))
    const endIdx    = Math.min(Math.round(endFrac * (len - 1)), len - 1)

    const open  = prices[startIdx]
    const close = prices[endIdx]

    // Local volatility window (±2 neighbours) to size the wicks
    const wStart = Math.max(0, startIdx - 2)
    const wEnd   = Math.min(len - 1, endIdx + 2)
    const window = prices.slice(wStart, wEnd + 1)
    const wMax   = Math.max(...window)
    const wMin   = Math.min(...window)
    const range  = wMax - wMin || Math.abs(open) * 0.01 || 1

    // Wicks seeded by session + candle index → different every page load
    const upperWick = range * (0.2 + seededRand(sessionSeed, i * 13 + 1) * 0.6)
    const lowerWick = range * (0.2 + seededRand(sessionSeed, i * 17 + 3) * 0.6)

    return {
      open,
      close,
      high: Math.max(open, close) + upperWick,
      low:  Math.min(open, close) - lowerWick,
    }
  })
}

// ─── Nice axis step ───────────────────────────────────────────────────────────
function niceStep(range: number, ticks: number): number {
  const raw  = range / ticks
  const mag  = Math.pow(10, Math.floor(Math.log10(raw)))
  const norm = raw / mag
  const nice = norm < 1.5 ? 1 : norm < 3 ? 2 : norm < 7 ? 5 : 10
  return nice * mag
}

// ─── Component ────────────────────────────────────────────────────────────────
export function CandleChart({
  data,
  candles: candleCount = 30,
  height = 220,
}: CandleChartProps) {
  // Initialised once per mount from Date.now() → different every page refresh,
  // but stable during the session so re-renders don't reshuffle the chart.
  const sessionSeed = useRef(Date.now() % 99991).current

  const candles = useMemo(
    () => buildCandles(data, candleCount, sessionSeed),
    [data, candleCount, sessionSeed]
  )

  // Fixed viewBox dimensions — SVG scales to container width via width="100%"
  // Using a wide viewBox so each candle body is several units wide
  const VB_W   = 900
  const VB_H   = 260
  const PAD    = { top: 16, right: 64, bottom: 28, left: 12 }
  const PLOT_W = VB_W - PAD.left - PAD.right   // 824
  const PLOT_H = VB_H - PAD.top - PAD.bottom   // 216

  const priceMin = useMemo(() => Math.min(...candles.map(c => c.low)),  [candles])
  const priceMax = useMemo(() => Math.max(...candles.map(c => c.high)), [candles])
  const range    = priceMax - priceMin || 1
  const yMin     = priceMin - range * 0.06
  const yMax     = priceMax + range * 0.06
  const yRange   = yMax - yMin

  const toY = (p: number) => PAD.top + ((yMax - p) / yRange) * PLOT_H

  // Slot = total horizontal space per candle; body = 55% of slot
  const slot   = PLOT_W / candles.length
  const bodyW  = Math.max(4, slot * 0.55)
  const wickW  = Math.max(1.5, bodyW * 0.18)

  // Y-axis ticks
  const step      = niceStep(yRange, 5)
  const tickStart = Math.ceil(yMin / step) * step
  const ticks: number[] = []
  for (let t = tickStart; t <= yMax + step * 0.01; t += step) ticks.push(t)

  const fmt = (v: number) => {
    if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(2)}M`
    if (v >= 1_000)     return `${(v / 1_000).toFixed(1)}k`
    if (v >= 1)         return v.toFixed(1)
    return v.toFixed(4)
  }

  if (candles.length === 0) {
    return (
      <div
        className="bg-surface-container-low rounded-xl border border-outline-variant/15 p-4 flex items-center justify-center"
        style={{ height }}
      >
        <p className="text-xs text-on-surface-variant font-body">No chart data</p>
      </div>
    )
  }

  return (
    <div className="bg-surface-container-low rounded-xl border border-outline-variant/15 overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-outline-variant/10">
        <span className="text-[10px] font-headline font-semibold text-on-surface-variant uppercase tracking-wider">
          Candlestick · {candles.length}D
        </span>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-sm bg-[#10b981]" />
            <span className="text-[10px] font-headline text-on-surface-variant">Bullish</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-sm bg-[#ef4444]" />
            <span className="text-[10px] font-headline text-on-surface-variant">Bearish</span>
          </div>
        </div>
      </div>

      {/* SVG — uniform scaling, no distortion */}
      <svg
        viewBox={`0 0 ${VB_W} ${VB_H}`}
        width="100%"
        height={height}
        aria-label="Candlestick price chart"
        role="img"
      >
        {/* Grid lines */}
        {ticks.map(t => (
          <line
            key={t}
            x1={PAD.left}  y1={toY(t)}
            x2={VB_W - PAD.right} y2={toY(t)}
            stroke="rgba(255,255,255,0.06)"
            strokeWidth={0.6}
          />
        ))}

        {/* Price labels */}
        {ticks.map(t => (
          <text
            key={`l${t}`}
            x={VB_W - PAD.right + 6}
            y={toY(t) + 4}
            fontSize={10}
            fill="rgba(255,255,255,0.4)"
            fontFamily="monospace"
          >
            {fmt(t)}
          </text>
        ))}

        {/* Candles */}
        {candles.map((c, i) => {
          const bullish = c.close >= c.open
          const color   = bullish ? '#10b981' : '#ef4444'
          const cx      = PAD.left + i * slot + slot / 2

          const bodyTop = toY(Math.max(c.open, c.close))
          const bodyBot = toY(Math.min(c.open, c.close))
          const bodyH   = Math.max(2, bodyBot - bodyTop)   // never collapse to 0

          return (
            <g key={i}>
              {/* Full wick (high → low) as single line behind body */}
              <line
                x1={cx} y1={toY(c.high)}
                x2={cx} y2={toY(c.low)}
                stroke={color}
                strokeWidth={wickW}
                opacity={0.85}
              />
              {/* Body rect */}
              <rect
                x={cx - bodyW / 2}
                y={bodyTop}
                width={bodyW}
                height={bodyH}
                fill={color}
                fillOpacity={0.9}
                rx={1.5}
              />
            </g>
          )
        })}

        {/* Baseline */}
        <line
          x1={PAD.left} y1={PAD.top + PLOT_H}
          x2={VB_W - PAD.right} y2={PAD.top + PLOT_H}
          stroke="rgba(255,255,255,0.1)"
          strokeWidth={0.6}
        />
      </svg>
    </div>
  )
}
