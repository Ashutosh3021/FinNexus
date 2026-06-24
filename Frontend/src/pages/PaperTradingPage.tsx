import { useState } from 'react'
import { useAppStore } from '../store/useAppStore'
import { PriceChart } from '../components/ui/PriceChart'
import { cn } from '../lib/utils'
import { Wallet, TrendingUp, TrendingDown, Minus, Bot, ChevronDown } from 'lucide-react'
import type { Asset, PaperTrade } from '../types'

export function PaperTradingPage() {
  const { assets, user, trades, executeTrade } = useAppStore()
  const [selectedAsset, setSelectedAsset] = useState<Asset>(assets[0])
  const [amount] = useState(20)
  const [showDropdown, setShowDropdown] = useState(false)
  const [lastTrade, setLastTrade] = useState<PaperTrade | null>(null)

  const currentPrediction = useAppStore(s => s.predictions.find(p => p.assetId === selectedAsset.id))
  const botAction = currentPrediction?.signal === 'BUY' ? 'BUY' :
                    currentPrediction?.signal === 'SELL' ? 'SELL' : 'HOLD'

  const cash = user?.paperCash ?? 100

  const handleTrade = (type: 'BUY' | 'SELL' | 'HOLD') => {
    if (type === 'HOLD') return
    if (cash < amount) return

    const trade = {
      assetId: selectedAsset.id,
      assetName: selectedAsset.name,
      assetSymbol: selectedAsset.symbol,
      type,
      amount,
      price: selectedAsset.price,
      botAction,
    }
    executeTrade(trade as Parameters<typeof executeTrade>[0])
    // Simulate resolved trade for demo
    const resolved: PaperTrade = {
      ...trade,
      id: `trade-${Date.now()}`,
      userResult: type !== botAction ? 'WIN' : 'LOSS',
      botResult: type !== botAction ? 'LOSS' : 'WIN',
      analysis: {
        actualOutcome: `${selectedAsset.name} moved ${selectedAsset.change > 0 ? '+' : ''}${selectedAsset.changeFormatted} in the period.`,
        userReason: type === 'BUY'
          ? 'User identified positive momentum signals and entered long.'
          : 'User anticipated a reversal from recent highs.',
        botReason: `Bot predicted ${botAction} based on ${currentPrediction?.reasoning?.slice(0, 80) ?? 'technical analysis'}.`,
        lesson: type !== botAction
          ? 'Human intuition combined with market context can outperform pure algorithmic signals.'
          : 'Aligning with model consensus generally improves outcomes.',
        priceAtClose: selectedAsset.price * (1 + selectedAsset.change / 100),
        pnlPercent: selectedAsset.change,
      },
      timestamp: new Date().toISOString(),
      resolvedAt: new Date().toISOString(),
      botAction: botAction as 'BUY' | 'SELL' | 'HOLD',
    }
    setLastTrade(resolved)
  }

  const recentTrades = trades.slice(0, 5)

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="font-headline font-bold text-2xl text-on-surface">Paper Trading</h1>
          <p className="text-sm text-on-surface-variant mt-0.5">Practice with paper cash. No real money at risk.</p>
        </div>
        <div className="flex items-center gap-2 bg-surface-container-low rounded-xl border border-primary/20 px-4 py-2.5">
          <Wallet size={14} className="text-primary" />
          <div>
            <p className="text-[10px] text-on-surface-variant font-headline uppercase tracking-wider">Paper Cash</p>
            <p className="font-data font-bold text-primary text-lg">₹{cash}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Trading panel */}
        <div className="lg:col-span-2 space-y-4">
          {/* Asset selector */}
          <div className="bg-surface-container-low rounded-xl border border-outline-variant/15 p-4">
            <label className="text-xs font-headline text-on-surface-variant uppercase tracking-wider block mb-2">Select Asset</label>
            <div className="relative">
              <button
                onClick={() => setShowDropdown(!showDropdown)}
                className="w-full flex items-center justify-between bg-surface-container-high border border-outline-variant/20 rounded-lg px-3 py-2.5 text-sm text-on-surface hover:border-outline-variant/40 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <span className="font-data font-bold text-primary">{selectedAsset.symbol}</span>
                  <span className="font-headline">{selectedAsset.name}</span>
                  <span className={cn('text-xs font-data', selectedAsset.change >= 0 ? 'text-primary' : 'text-error')}>
                    {selectedAsset.changeFormatted}
                  </span>
                </div>
                <ChevronDown size={14} className="text-on-surface-variant" />
              </button>
              {showDropdown && (
                <div className="absolute top-full mt-1 left-0 right-0 bg-surface-container z-30 rounded-lg border border-outline-variant/20 shadow-xl max-h-48 overflow-y-auto">
                  {assets.map(a => (
                    <button
                      key={a.id}
                      onClick={() => { setSelectedAsset(a); setShowDropdown(false) }}
                      className={cn(
                        'w-full flex items-center justify-between px-3 py-2.5 text-sm hover:bg-surface-container-high transition-colors',
                        selectedAsset.id === a.id && 'bg-primary/5 text-primary'
                      )}
                    >
                      <div className="flex items-center gap-2">
                        <span className="font-data font-bold text-xs w-16 text-left">{a.symbol}</span>
                        <span className="font-headline text-on-surface">{a.name}</span>
                      </div>
                      <span className={cn('text-xs font-data', a.change >= 0 ? 'text-primary' : 'text-error')}>{a.changeFormatted}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Chart */}
          <PriceChart
            data={selectedAsset.chartData}
            color={selectedAsset.change >= 0 ? '#10b981' : '#ef4444'}
          />

          {/* Bot vs User panel */}
          <div className="bg-surface-container-low rounded-xl border border-outline-variant/15 p-4">
            <div className="flex items-center gap-2 mb-3">
              <Bot size={14} className="text-on-surface-variant" />
              <span className="text-xs font-headline font-semibold text-on-surface uppercase tracking-wider">Bot's Position</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-surface-container-highest/50 rounded-lg">
              <div>
                <p className="text-xs text-on-surface-variant font-headline mb-0.5">Bot predicts</p>
                <span className={cn(
                  'text-lg font-headline font-bold',
                  botAction === 'BUY' ? 'text-primary' : botAction === 'SELL' ? 'text-error' : 'text-tertiary'
                )}>
                  {botAction}
                </span>
              </div>
              <div className="text-right">
                <p className="text-xs text-on-surface-variant font-headline mb-0.5">Confidence</p>
                <span className="text-lg font-data font-bold text-on-surface">{currentPrediction?.confidence ?? '–'}%</span>
              </div>
            </div>
            {currentPrediction && (
              <p className="text-xs text-on-surface-variant mt-3 leading-relaxed font-body">
                {currentPrediction.reasoning}
              </p>
            )}
          </div>

          {/* Trade buttons */}
          <div className="bg-surface-container-low rounded-xl border border-outline-variant/15 p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-headline text-on-surface-variant uppercase tracking-wider">Your Call</span>
              <span className="text-xs font-data text-on-surface-variant">Amount: ₹{amount}</span>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <TradeButton
                label="BUY"
                icon={<TrendingUp size={16} />}
                color="primary"
                disabled={cash < amount}
                onClick={() => handleTrade('BUY')}
              />
              <TradeButton
                label="HOLD"
                icon={<Minus size={16} />}
                color="tertiary"
                onClick={() => handleTrade('HOLD')}
              />
              <TradeButton
                label="SELL"
                icon={<TrendingDown size={16} />}
                color="error"
                disabled={cash < amount}
                onClick={() => handleTrade('SELL')}
              />
            </div>
            {cash < amount && (
              <p className="text-xs text-error text-center mt-2 font-body">Insufficient paper cash. Contribute to earn more.</p>
            )}
          </div>
        </div>

        {/* Trade history + analysis */}
        <div className="space-y-4">
          {/* Post-trade analysis */}
          {lastTrade && lastTrade.analysis && (
            <div className={cn(
              'rounded-xl border p-4 space-y-3',
              lastTrade.userResult === 'WIN' ? 'border-primary/30 bg-primary/5' : 'border-error/30 bg-error/5'
            )}>
              <div className="flex items-center gap-2">
                <span className={cn('text-sm font-headline font-bold', lastTrade.userResult === 'WIN' ? 'text-primary' : 'text-error')}>
                  {lastTrade.userResult === 'WIN' ? '✓ You Won' : '✗ Bot Won'}
                </span>
                <span className="text-xs text-on-surface-variant">vs Bot: {lastTrade.botResult}</span>
              </div>
              <div className="space-y-2 text-xs">
                <AnalysisRow label="Actual Outcome" value={lastTrade.analysis.actualOutcome} />
                <AnalysisRow label="Your Move" value={lastTrade.analysis.userReason} />
                <AnalysisRow label="Bot's Logic" value={lastTrade.analysis.botReason} />
                <div className="bg-surface-container-highest/60 rounded p-2.5 border border-outline-variant/10">
                  <p className="text-[10px] font-headline text-on-surface-variant uppercase tracking-wider mb-1">Lesson</p>
                  <p className="text-on-surface font-body">{lastTrade.analysis.lesson}</p>
                </div>
              </div>
            </div>
          )}

          {/* Recent trades */}
          <div className="bg-surface-container-low rounded-xl border border-outline-variant/15 p-4">
            <h3 className="font-headline font-semibold text-sm text-on-surface mb-3">Recent Trades</h3>
            {recentTrades.length === 0 ? (
              <p className="text-xs text-on-surface-variant font-body text-center py-4">No trades yet. Make your first call!</p>
            ) : (
              <div className="space-y-2">
                {recentTrades.map(t => (
                  <div key={t.id} className="flex items-center justify-between py-2 border-b border-outline-variant/8 last:border-0">
                    <div>
                      <p className="text-xs font-headline font-medium text-on-surface">{t.assetName}</p>
                      <p className={cn('text-[10px] font-data font-bold', t.type === 'BUY' ? 'text-primary' : 'text-error')}>
                        {t.type}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs font-data text-on-surface-variant">₹{t.amount}</p>
                      {t.userResult && (
                        <p className={cn('text-[10px] font-headline font-bold', t.userResult === 'WIN' ? 'text-primary' : 'text-error')}>
                          {t.userResult}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function TradeButton({ label, icon, color, disabled, onClick }: {
  label: string; icon: React.ReactNode; color: 'primary' | 'tertiary' | 'error'; disabled?: boolean; onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'flex flex-col items-center gap-1.5 py-3 rounded-xl border font-headline font-bold text-sm transition-all active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed',
        color === 'primary' ? 'border-primary/30 text-primary hover:bg-primary/10 bg-primary/5' :
        color === 'tertiary' ? 'border-tertiary/30 text-tertiary hover:bg-tertiary/10 bg-tertiary/5' :
        'border-error/30 text-error hover:bg-error/10 bg-error/5'
      )}
    >
      {icon}
      {label}
    </button>
  )
}

function AnalysisRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10px] font-headline text-on-surface-variant uppercase tracking-wider mb-0.5">{label}</p>
      <p className="text-on-surface font-body leading-relaxed">{value}</p>
    </div>
  )
}
