import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppStore } from '../store/useAppStore'
import { ConfidenceRing } from '../components/ui/ConfidenceRing'
import { cn } from '../lib/utils'
import { Brain, Cpu, BookOpen, Bot, Clock, Activity } from 'lucide-react'
import type { Prediction, Asset } from '../types'

export function PredictionsPage() {
  const { predictions, assets } = useAppStore()
  const navigate = useNavigate()
  const [analyzedSymbol, setAnalyzedSymbol] = useState<string | null>(null)

  const handleAnalyze = (symbol: string) => {
    setAnalyzedSymbol(symbol)
    // Navigate to trends page filtered to this asset's class, or stay on page
    // For now scroll into a detailed view on the same page
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-headline font-bold text-2xl text-on-surface">System Predictions</h1>
        <p className="text-sm text-on-surface-variant mt-0.5">Combined ML + RAG + Bot signals with confidence scores</p>
      </div>

      {/* Model legend */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <ModelBadge icon={<Cpu size={14} />} label="ML Model" desc="Pattern recognition & price prediction" color="primary" />
        <ModelBadge icon={<BookOpen size={14} />} label="RAG Engine" desc="News & fundamentals analysis" color="tertiary" />
        <ModelBadge icon={<Bot size={14} />} label="Trading Bot" desc="Momentum & technical signals" color="secondary" />
      </div>

      {/* Analyze panel — shown when a symbol is selected */}
      {analyzedSymbol && (
        <div className="bg-surface-container-low rounded-xl border border-primary/20 p-4 flex items-start gap-3">
          <Activity size={14} className="text-primary shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-headline font-semibold text-on-surface">
              Analysing {analyzedSymbol}
            </p>
            <p className="text-xs text-on-surface-variant mt-1">
              Detailed signal breakdown: ML model predicts based on momentum, RSI, and MACD.
              RAG engine cross-references recent news and macro events.
              Bot signals confirm with volume and trend indicators.
            </p>
          </div>
          <button
            onClick={() => setAnalyzedSymbol(null)}
            className="text-[10px] font-headline text-on-surface-variant hover:text-on-surface transition-colors shrink-0"
          >
            ✕
          </button>
        </div>
      )}

      {/* Prediction cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {predictions.map(pred => {
          const asset = assets.find(a => a.id === pred.assetId)
          if (!asset) return null
          return (
            <PredictionCard
              key={pred.assetId}
              prediction={pred}
              asset={asset}
              onAnalyze={handleAnalyze}
              isAnalyzed={analyzedSymbol === asset.symbol}
            />
          )
        })}
      </div>
    </div>
  )
}

function ModelBadge({ icon, label, desc, color }: {
  icon: React.ReactNode; label: string; desc: string; color: 'primary' | 'tertiary' | 'secondary'
}) {
  return (
    <div className={cn(
      'bg-surface-container-low rounded-xl p-3 border flex items-start gap-3',
      color === 'primary' ? 'border-primary/15' :
      color === 'tertiary' ? 'border-tertiary/15' : 'border-outline-variant/15'
    )}>
      <div className={cn(
        'w-7 h-7 rounded flex items-center justify-center shrink-0',
        color === 'primary' ? 'bg-primary/10 text-primary' :
        color === 'tertiary' ? 'bg-tertiary/10 text-tertiary' : 'bg-secondary/10 text-secondary'
      )}>
        {icon}
      </div>
      <div>
        <p className="text-xs font-headline font-semibold text-on-surface">{label}</p>
        <p className="text-[10px] text-on-surface-variant">{desc}</p>
      </div>
    </div>
  )
}

function PredictionCard({ prediction: p, asset, onAnalyze, isAnalyzed }: {
  prediction: Prediction
  asset: Asset
  onAnalyze: (symbol: string) => void
  isAnalyzed?: boolean
}) {
  const variant = p.signal === 'BUY' ? 'invest' : p.signal === 'HOLD' ? 'hold' : 'skip'

  const signalColor = {
    BUY: 'text-primary bg-primary/10 border-primary/20',
    HOLD: 'text-tertiary bg-tertiary/10 border-tertiary/20',
    SELL: 'text-error bg-error/10 border-error/20',
  }[p.signal]

  const subSignalColor = (s: string) => ({
    BUY: 'text-primary', HOLD: 'text-tertiary', SELL: 'text-error'
  })[s] ?? 'text-on-surface-variant'

  return (
    <div className={cn(
      'bg-surface-container-low rounded-xl border p-5 flex flex-col gap-4 transition-all hover:shadow-[0_0_20px_rgba(16,185,129,0.05)]',
      isAnalyzed ? 'ring-1 ring-primary/40' : '',
      p.signal === 'BUY' ? 'border-primary/15' :
      p.signal === 'SELL' ? 'border-error/15' : 'border-tertiary/15'
    )}>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded bg-surface-container-highest border border-outline-variant/15 flex items-center justify-center">
            <span className="text-xs font-data font-bold text-on-surface">{asset.symbol.slice(0, 4)}</span>
          </div>
          <div>
            <p className="font-headline font-semibold text-on-surface">{asset.name}</p>
            <p className="text-xs text-on-surface-variant font-data">{asset.priceFormatted}</p>
          </div>
        </div>
        <span className={cn('text-xs font-headline font-bold px-2.5 py-1 rounded border', signalColor)}>
          {p.signal}
        </span>
      </div>

      {/* Confidence ring + score */}
      <div className="flex items-center gap-5">
        <ConfidenceRing value={p.confidence} variant={variant} size="md" />
        <div className="flex-1 space-y-3">
          {/* Sub-signals */}
          <div className="space-y-1.5">
            {[
              { label: 'ML Model', signal: p.mlSignal, icon: <Cpu size={11} /> },
              { label: 'RAG Engine', signal: p.ragSignal, icon: <BookOpen size={11} /> },
              { label: 'Bot', signal: p.botSignal, icon: <Bot size={11} /> },
            ].map(({ label, signal, icon }) => (
              <div key={label} className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-on-surface-variant">
                  {icon}
                  <span className="text-[11px] font-headline">{label}</span>
                </div>
                <span className={cn('text-[11px] font-data font-bold', subSignalColor(signal))}>
                  {signal}
                </span>
              </div>
            ))}
          </div>

          {/* Model performance */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] font-headline text-on-surface-variant uppercase tracking-wider">Model Performance</span>
              <span className="text-[10px] font-data text-on-surface">{p.modelPerformance}%</span>
            </div>
            <div className="h-1 bg-surface-container-highest rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-primary to-primary-container rounded-full transition-all"
                style={{ width: `${p.modelPerformance}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Reasoning */}
      <div className="bg-surface-container-highest/60 rounded-lg p-3 border border-outline-variant/10">
        <div className="flex items-center gap-1.5 mb-1.5">
          <Brain size={11} className="text-on-surface-variant" />
          <span className="text-[10px] font-headline text-on-surface-variant uppercase tracking-wider">Reasoning</span>
        </div>
        <p className="text-xs text-on-surface-variant font-body leading-relaxed">{p.reasoning}</p>
      </div>

      {/* Timestamp */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-[10px] text-on-surface-variant font-data">
          <Clock size={10} />
          Last updated {p.timestamp}
        </div>
        <button
          onClick={() => onAnalyze(asset.symbol)}
          className="text-xs font-headline font-semibold text-primary hover:text-primary-container transition-colors flex items-center gap-1 active:scale-95"
          aria-label={`Analyze ${asset.symbol}`}
        >
          Analyze <Activity size={14} />
        </button>
      </div>
    </div>
  )
}
