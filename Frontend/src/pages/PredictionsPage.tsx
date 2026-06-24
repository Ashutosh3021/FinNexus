import { useAppStore } from '../store/useAppStore'
import { ConfidenceRing } from '../components/ui/ConfidenceRing'
import { cn } from '../lib/utils'
import { Brain, Cpu, BookOpen, Bot, Clock } from 'lucide-react'
import type { Prediction, Asset } from '../types'

export function PredictionsPage() {
  const { predictions, assets } = useAppStore()

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

      {/* Prediction cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {predictions.map(pred => {
          const asset = assets.find(a => a.id === pred.assetId)
          if (!asset) return null
          return <PredictionCard key={pred.assetId} prediction={pred} asset={asset} />
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

function PredictionCard({ prediction: p, asset }: { prediction: Prediction; asset: Asset }) {
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
      <div className="flex items-center gap-1.5 text-[10px] text-on-surface-variant font-data">
        <Clock size={10} />
        Last updated {p.timestamp}
      </div>
    </div>
  )
}
