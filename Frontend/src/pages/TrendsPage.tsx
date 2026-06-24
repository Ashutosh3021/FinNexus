import { useState } from 'react'
import { useAppStore } from '../store/useAppStore'
import { cn } from '../lib/utils'
import type { Timeframe, AssetClass, Asset } from '../types'

const TIMEFRAMES: Timeframe[] = ['1D', '1W', '1M']
const CLASS_TABS: (AssetClass | 'All')[] = ['All', 'Stocks', 'Crypto', 'ETFs', 'Futures', 'Commodities']

// Simulate different trend signals per timeframe
function getTrendForTimeframe(asset: Asset, tf: Timeframe) {
  const map: Record<string, Record<Timeframe, typeof asset.trend>> = {
    btc:      { '1D': 'Bullish',  '1W': 'Bullish',  '1M': 'Bullish' },
    eth:      { '1D': 'Neutral',  '1W': 'Bullish',  '1M': 'Neutral' },
    sol:      { '1D': 'Bearish',  '1W': 'Bearish',  '1M': 'Neutral' },
    bnb:      { '1D': 'Bullish',  '1W': 'Neutral',  '1M': 'Bullish' },
    reliance: { '1D': 'Bullish',  '1W': 'Bullish',  '1M': 'Bullish' },
    tcs:      { '1D': 'Neutral',  '1W': 'Neutral',  '1M': 'Bullish' },
    hdfc:     { '1D': 'Bullish',  '1W': 'Neutral',  '1M': 'Bullish' },
    infosys:  { '1D': 'Bearish',  '1W': 'Neutral',  '1M': 'Neutral' },
    spy:      { '1D': 'Bullish',  '1W': 'Bullish',  '1M': 'Bullish' },
    qqq:      { '1D': 'Bullish',  '1W': 'Bullish',  '1M': 'Bullish' },
    gld:      { '1D': 'Neutral',  '1W': 'Bullish',  '1M': 'Neutral' },
    nifty50:  { '1D': 'Bullish',  '1W': 'Bullish',  '1M': 'Bullish' },
    banknifty:{ '1D': 'Neutral',  '1W': 'Bearish',  '1M': 'Neutral' },
    gold:     { '1D': 'Bullish',  '1W': 'Bullish',  '1M': 'Neutral' },
    crude:    { '1D': 'Bearish',  '1W': 'Bearish',  '1M': 'Neutral' },
    silver:   { '1D': 'Bullish',  '1W': 'Neutral',  '1M': 'Bullish' },
  }
  return map[asset.id]?.[tf] ?? asset.trend
}

export function TrendsPage() {
  const { assets } = useAppStore()
  const [timeframe, setTimeframe] = useState<Timeframe>('1D')
  const [filter, setFilter] = useState<AssetClass | 'All'>('All')

  const filtered = (filter === 'All' ? assets : assets.filter(a => a.assetClass === filter))
    .map(a => ({ ...a, currentTrend: getTrendForTimeframe(a, timeframe) }))

  const bullish = filtered.filter(a => a.currentTrend === 'Bullish')
  const bearish = filtered.filter(a => a.currentTrend === 'Bearish')
  const neutral  = filtered.filter(a => a.currentTrend === 'Neutral')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="font-headline font-bold text-2xl text-on-surface">Recent Trends</h1>
        <p className="text-sm text-on-surface-variant mt-0.5">Visual trend signals across all tracked assets</p>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap gap-3 items-center justify-between">
        {/* Timeframe */}
        <div className="flex gap-1 bg-surface-container-low rounded-lg p-1 border border-outline-variant/15">
          {TIMEFRAMES.map(tf => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={cn(
                'px-4 py-1.5 rounded text-xs font-headline font-semibold transition-all',
                timeframe === tf ? 'bg-primary text-on-primary shadow-sm' : 'text-on-surface-variant hover:text-on-surface'
              )}
            >
              {tf}
            </button>
          ))}
        </div>

        {/* Class filter */}
        <div className="flex gap-1.5 overflow-x-auto scrollbar-hide">
          {CLASS_TABS.map(cls => (
            <button
              key={cls}
              onClick={() => setFilter(cls)}
              className={cn(
                'px-3 py-1.5 rounded-lg text-xs font-headline font-medium whitespace-nowrap transition-all border',
                filter === cls ? 'bg-primary/10 text-primary border-primary/30' : 'border-outline-variant/20 text-on-surface-variant hover:text-on-surface'
              )}
            >
              {cls}
            </button>
          ))}
        </div>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-3 gap-3">
        <StatCard label="Bullish ↥" value={bullish.length} color="primary" />
        <StatCard label="Neutral –" value={neutral.length} color="tertiary" />
        <StatCard label="Bearish ↧" value={bearish.length} color="error" />
      </div>

      {/* Trend groups */}
      {[
        { label: 'Bullish ↥', items: bullish, color: 'primary' as const },
        { label: 'Neutral –', items: neutral, color: 'tertiary' as const },
        { label: 'Bearish ↧', items: bearish, color: 'error' as const },
      ].map(({ label, items, color }) =>
        items.length > 0 && (
          <section key={label}>
            <div className={cn(
              'flex items-center gap-2 mb-3',
            )}>
              <div className={cn(
                'w-2 h-2 rounded-full',
                color === 'primary' ? 'bg-primary shadow-[0_0_6px_rgba(16,185,129,0.5)]' :
                color === 'error' ? 'bg-error shadow-[0_0_6px_rgba(255,70,70,0.4)]' :
                'bg-tertiary shadow-[0_0_6px_rgba(255,185,95,0.4)]'
              )} />
              <h2 className={cn(
                'text-xs font-headline font-semibold uppercase tracking-widest',
                color === 'primary' ? 'text-primary' : color === 'error' ? 'text-error' : 'text-tertiary'
              )}>{label} · {items.length} assets</h2>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {items.map(asset => (
                <TrendCard key={asset.id} asset={asset} trend={asset.currentTrend} timeframe={timeframe} />
              ))}
            </div>
          </section>
        )
      )}
    </div>
  )
}

function StatCard({ label, value, color }: { label: string; value: number; color: 'primary' | 'tertiary' | 'error' }) {
  return (
    <div className={cn(
      'bg-surface-container-low rounded-xl p-4 border text-center',
      color === 'primary' ? 'border-primary/20' :
      color === 'error' ? 'border-error/20' : 'border-tertiary/20'
    )}>
      <p className={cn(
        'text-2xl font-data font-bold',
        color === 'primary' ? 'text-primary' : color === 'error' ? 'text-error' : 'text-tertiary'
      )}>{value}</p>
      <p className="text-xs text-on-surface-variant font-headline mt-0.5">{label}</p>
    </div>
  )
}

function TrendCard({ asset, trend, timeframe }: {
  asset: Asset & { currentTrend: string }
  trend: string
  timeframe: Timeframe
}) {
  const isUp = trend === 'Bullish'
  const isDown = trend === 'Bearish'

  // Mini bar chart using last 7 prices
  const recentPrices = asset.chartData.slice(-7)
  const maxP = Math.max(...recentPrices.map(p => p.price))
  const minP = Math.min(...recentPrices.map(p => p.price))

  return (
    <div className={cn(
      'bg-surface-container-low rounded-xl p-4 border transition-all hover:border-opacity-50',
      isUp ? 'border-primary/20 hover:border-primary/40' :
      isDown ? 'border-error/20 hover:border-error/40' : 'border-outline-variant/20 hover:border-outline-variant/40'
    )}>
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="font-headline font-semibold text-sm text-on-surface">{asset.name}</p>
          <p className="text-xs text-on-surface-variant font-data">{asset.symbol}</p>
        </div>
        <div className={cn(
          'text-xl font-bold leading-none',
          isUp ? 'text-primary' : isDown ? 'text-error' : 'text-tertiary'
        )}>
          {isUp ? '↥' : isDown ? '↧' : '—'}
        </div>
      </div>

      {/* Mini sparkline */}
      <div className="flex items-end gap-0.5 h-8 mb-3">
        {recentPrices.map((p, i) => {
          const h = maxP === minP ? 50 : Math.round(((p.price - minP) / (maxP - minP)) * 100)
          const isLast = i === recentPrices.length - 1
          return (
            <div
              key={i}
              className={cn(
                'flex-1 rounded-sm transition-all',
                isLast ? (isUp ? 'bg-primary' : isDown ? 'bg-error' : 'bg-tertiary') :
                (isUp ? 'bg-primary/30' : isDown ? 'bg-error/30' : 'bg-tertiary/30')
              )}
              style={{ height: `${Math.max(h, 10)}%` }}
            />
          )
        })}
      </div>

      <div className="flex items-center justify-between">
        <span className="text-xs font-data text-on-surface-variant">{asset.priceFormatted}</span>
        <span className={cn(
          'text-xs font-headline font-semibold px-2 py-0.5 rounded',
          isUp ? 'bg-primary/10 text-primary' : isDown ? 'bg-error/10 text-error' : 'bg-tertiary/10 text-tertiary'
        )}>
          {trend} · {timeframe}
        </span>
      </div>
    </div>
  )
}
