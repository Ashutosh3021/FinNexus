import { useState } from 'react'
import { ArrowUpRight, ArrowDownRight, Minus, RefreshCw, Clock } from 'lucide-react'
import { useAppStore } from '../store/useAppStore'
import { PriceChart } from '../components/ui/PriceChart'
import { cn } from '../lib/utils'
import type { Asset, AssetClass } from '../types'

const CLASS_TABS: (AssetClass | 'All')[] = ['All', 'Stocks', 'Crypto', 'ETFs', 'Futures', 'Commodities']

export function PricesPage() {
  const { assets, selectedAssetClass, setAssetClass, isLoading, simulateRefresh, lastPriceUpdate } = useAppStore()
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null)

  const filtered = selectedAssetClass === 'All' ? assets : assets.filter(a => a.assetClass === selectedAssetClass)

  // Group by class for display
  const grouped: Record<string, Asset[]> = {}
  if (selectedAssetClass === 'All') {
    for (const cls of ['Crypto', 'Stocks', 'ETFs', 'Futures', 'Commodities']) {
      const items = assets.filter(a => a.assetClass === cls)
      if (items.length) grouped[cls] = items
    }
  } else {
    grouped[selectedAssetClass] = filtered
  }

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="font-headline font-bold text-2xl text-on-surface">Live Prices</h1>
          <p className="text-sm text-on-surface-variant mt-0.5 flex items-center gap-1.5">
            <Clock size={12} />
            Last updated {lastPriceUpdate}
          </p>
        </div>
        <button
          onClick={simulateRefresh}
          disabled={isLoading}
          className="flex items-center gap-2 text-sm font-headline text-primary hover:text-primary-container transition-colors disabled:opacity-50 self-start sm:self-auto"
        >
          <RefreshCw size={14} className={cn(isLoading && 'animate-spin')} />
          Refresh
        </button>
      </div>

      {/* Class filter tabs */}
      <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-hide">
        {CLASS_TABS.map((cls) => (
          <button
            key={cls}
            onClick={() => setAssetClass(cls)}
            className={cn(
              'px-3 py-1.5 rounded-lg text-xs font-headline font-medium whitespace-nowrap transition-all border',
              selectedAssetClass === cls
                ? 'bg-primary/10 text-primary border-primary/30'
                : 'border-outline-variant/20 text-on-surface-variant hover:text-on-surface hover:border-outline-variant/40'
            )}
          >
            {cls}
          </button>
        ))}
      </div>

      {/* Chart panel if asset selected */}
      {selectedAsset && (
        <div className="bg-surface-container-low rounded-xl border border-outline-variant/15 p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded bg-surface-container-highest border border-outline-variant/15 flex items-center justify-center">
                <span className="text-xs font-data font-bold text-on-surface">{selectedAsset.symbol.slice(0, 3)}</span>
              </div>
              <div>
                <p className="font-headline font-semibold text-on-surface">{selectedAsset.name}</p>
                <p className="text-xs text-on-surface-variant font-data">{selectedAsset.priceFormatted}</p>
              </div>
            </div>
            <button
              onClick={() => setSelectedAsset(null)}
              className="text-xs text-on-surface-variant hover:text-on-surface transition-colors font-headline"
            >
              Close ✕
            </button>
          </div>
          <PriceChart data={selectedAsset.chartData} color={selectedAsset.change >= 0 ? '#10b981' : '#ef4444'} />
        </div>
      )}

      {/* Asset groups */}
      {Object.entries(grouped).map(([cls, items]) => (
        <section key={cls}>
          <h2 className="text-xs font-headline font-semibold text-secondary uppercase tracking-widest mb-3 opacity-70">{cls}</h2>
          <div className="bg-surface-container-low rounded-xl border border-outline-variant/15 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-outline-variant/10">
                    <th className="text-left py-2.5 px-4 text-xs font-headline text-on-surface-variant uppercase tracking-wider">Asset</th>
                    <th className="text-right py-2.5 px-4 text-xs font-headline text-on-surface-variant uppercase tracking-wider">Price</th>
                    <th className="text-right py-2.5 px-4 text-xs font-headline text-on-surface-variant uppercase tracking-wider">24h Change</th>
                    <th className="text-right py-2.5 px-4 text-xs font-headline text-on-surface-variant uppercase tracking-wider hidden sm:table-cell">Volume</th>
                    <th className="text-right py-2.5 px-4 text-xs font-headline text-on-surface-variant uppercase tracking-wider hidden md:table-cell">Trend</th>
                    <th className="py-2.5 px-4 w-10"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-outline-variant/8">
                  {items.map((asset) => (
                    <AssetRow
                      key={asset.id}
                      asset={asset}
                      selected={selectedAsset?.id === asset.id}
                      onSelect={() => setSelectedAsset(selectedAsset?.id === asset.id ? null : asset)}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      ))}
    </div>
  )
}

function AssetRow({ asset, selected, onSelect }: { asset: Asset; selected: boolean; onSelect: () => void }) {
  const isUp = asset.change > 0
  const isFlat = asset.change === 0

  return (
    <tr
      className={cn(
        'hover:bg-surface-container-high/50 transition-colors cursor-pointer',
        selected && 'bg-primary/5'
      )}
      onClick={onSelect}
    >
      <td className="py-3 px-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-surface-container-highest border border-outline-variant/15 flex items-center justify-center shrink-0">
            <span className="text-[10px] font-data font-bold text-on-surface">{asset.symbol.slice(0, 4)}</span>
          </div>
          <div>
            <p className="text-sm font-headline font-medium text-on-surface">{asset.name}</p>
            <p className="text-xs text-on-surface-variant font-data">{asset.symbol}</p>
          </div>
        </div>
      </td>
      <td className="py-3 px-4 text-right">
        <span className="font-data font-bold text-sm text-on-surface">{asset.priceFormatted}</span>
      </td>
      <td className="py-3 px-4 text-right">
        <span className={cn(
          'inline-flex items-center gap-0.5 font-data text-sm font-medium',
          isUp ? 'text-primary' : isFlat ? 'text-on-surface-variant' : 'text-error'
        )}>
          {isFlat ? <Minus size={12} /> : isUp ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
          {asset.changeFormatted}
        </span>
      </td>
      <td className="py-3 px-4 text-right hidden sm:table-cell">
        <span className="text-xs text-on-surface-variant font-data">{asset.volume}</span>
      </td>
      <td className="py-3 px-4 text-right hidden md:table-cell">
        <TrendBadge trend={asset.trend} />
      </td>
      <td className="py-3 px-4">
        <div className={cn(
          'w-1.5 h-8 rounded-full transition-all',
          isUp ? 'bg-primary/40' : isFlat ? 'bg-outline-variant/30' : 'bg-error/40',
          selected && 'w-2 opacity-100'
        )} />
      </td>
    </tr>
  )
}

function TrendBadge({ trend }: { trend: string }) {
  return (
    <span className={cn(
      'text-[10px] font-headline font-semibold px-2 py-0.5 rounded border',
      trend === 'Bullish' ? 'text-primary border-primary/20 bg-primary/5' :
      trend === 'Bearish' ? 'text-error border-error/20 bg-error/5' :
      'text-on-surface-variant border-outline-variant/20'
    )}>
      {trend === 'Bullish' ? '↥' : trend === 'Bearish' ? '↧' : '–'} {trend}
    </span>
  )
}
