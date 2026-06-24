import { useAppStore } from '../store/useAppStore'
import { cn } from '../lib/utils'
import { CheckCircle2, XCircle, Clock, Target, TrendingUp, Award } from 'lucide-react'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip,
  CartesianGrid, ReferenceLine,
} from 'recharts'
import type { PredictionRecord } from '../types'

export function ConfidencePage() {
  const { predictionHistory, monthlyPerformance } = useAppStore()

  const resolved = predictionHistory.filter(p => p.correct !== null)
  const pending  = predictionHistory.filter(p => p.correct === null)
  const correct  = resolved.filter(p => p.correct)
  const accuracy = resolved.length > 0 ? Math.round((correct.length / resolved.length) * 100) : 0

  // Best performing assets
  const assetStats: Record<string, { total: number; correct: number }> = {}
  resolved.forEach(p => {
    if (!assetStats[p.assetName]) assetStats[p.assetName] = { total: 0, correct: 0 }
    assetStats[p.assetName].total++
    if (p.correct) assetStats[p.assetName].correct++
  })
  const bestAssets = Object.entries(assetStats)
    .map(([name, s]) => ({ name, accuracy: Math.round((s.correct / s.total) * 100), total: s.total }))
    .sort((a, b) => b.accuracy - a.accuracy)
    .slice(0, 5)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-headline font-bold text-2xl text-on-surface">Confidence & Learning</h1>
        <p className="text-sm text-on-surface-variant mt-0.5">Track prediction accuracy against real market outcomes</p>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard
          icon={<Target size={16} />}
          label="Accuracy"
          value={`${accuracy}%`}
          sub={`${correct.length} of ${resolved.length} correct`}
          color="primary"
        />
        <KpiCard
          icon={<TrendingUp size={16} />}
          label="Total Predictions"
          value={predictionHistory.length.toString()}
          sub={`Target: 20–30`}
          color={predictionHistory.length >= 20 ? 'primary' : 'tertiary'}
        />
        <KpiCard
          icon={<CheckCircle2 size={16} />}
          label="Resolved"
          value={resolved.length.toString()}
          sub={`${pending.length} pending`}
          color="primary"
        />
        <KpiCard
          icon={<Clock size={16} />}
          label="Pending"
          value={pending.length.toString()}
          sub="Awaiting outcome"
          color="tertiary"
        />
      </div>

      {/* Monthly performance chart */}
      <div className="bg-surface-container-low rounded-xl border border-outline-variant/15 p-5">
        <h2 className="font-headline font-semibold text-sm text-on-surface mb-4">Monthly Accuracy</h2>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={monthlyPerformance} barSize={28}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(134,148,138,0.1)" />
              <XAxis
                dataKey="month"
                axisLine={false} tickLine={false}
                tick={{ fill: '#bbcabf', fontSize: 11, fontFamily: 'Space Grotesk' }}
              />
              <YAxis
                domain={[0, 100]} axisLine={false} tickLine={false}
                tick={{ fill: '#bbcabf', fontSize: 11, fontFamily: 'IBM Plex Mono' }}
                tickFormatter={(v) => `${v}%`}
              />
              <Tooltip
                contentStyle={{ backgroundColor: '#111827', borderColor: 'rgba(134,148,138,0.15)', borderRadius: '8px' }}
                formatter={(v: number) => [`${v}%`, 'Accuracy']}
                labelStyle={{ color: '#dee1f7', fontFamily: 'Space Grotesk', fontSize: 12 }}
                itemStyle={{ color: '#10b981', fontFamily: 'IBM Plex Mono', fontSize: 12 }}
              />
              <ReferenceLine y={70} stroke="#10b981" strokeDasharray="4 4" strokeOpacity={0.4} label={{ value: '70% target', fill: '#10b981', fontSize: 10, fontFamily: 'Space Grotesk' }} />
              <Bar dataKey="accuracy" fill="#10b981" fillOpacity={0.8} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Two column: best assets + recent predictions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Best performing */}
        <div className="bg-surface-container-low rounded-xl border border-outline-variant/15 p-5">
          <div className="flex items-center gap-2 mb-4">
            <Award size={14} className="text-primary" />
            <h2 className="font-headline font-semibold text-sm text-on-surface">Best Performing Assets</h2>
          </div>
          <div className="space-y-3">
            {bestAssets.map((a, i) => (
              <div key={a.name} className="flex items-center gap-3">
                <span className="text-xs font-data text-on-surface-variant w-4">{i + 1}</span>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-0.5">
                    <span className="text-xs font-headline font-medium text-on-surface">{a.name}</span>
                    <span className="text-xs font-data font-bold text-primary">{a.accuracy}%</span>
                  </div>
                  <div className="h-1 bg-surface-container-highest rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary/60 rounded-full"
                      style={{ width: `${a.accuracy}%` }}
                    />
                  </div>
                </div>
                <span className="text-[10px] text-on-surface-variant font-data">{a.total}p</span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent prediction log */}
        <div className="bg-surface-container-low rounded-xl border border-outline-variant/15 p-5">
          <h2 className="font-headline font-semibold text-sm text-on-surface mb-4">Prediction Log</h2>
          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
            {predictionHistory.slice(0, 15).map(p => (
              <PredictionRow key={p.id} prediction={p} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function KpiCard({ icon, label, value, sub, color }: {
  icon: React.ReactNode; label: string; value: string; sub: string; color: 'primary' | 'tertiary'
}) {
  return (
    <div className={cn(
      'bg-surface-container-low rounded-xl p-4 border',
      color === 'primary' ? 'border-primary/15' : 'border-tertiary/15'
    )}>
      <div className={cn('mb-2', color === 'primary' ? 'text-primary' : 'text-tertiary')}>{icon}</div>
      <p className={cn('font-data font-bold text-2xl', color === 'primary' ? 'text-primary' : 'text-tertiary')}>{value}</p>
      <p className="text-xs font-headline font-medium text-on-surface mt-0.5">{label}</p>
      <p className="text-[10px] text-on-surface-variant mt-0.5 font-data">{sub}</p>
    </div>
  )
}

function PredictionRow({ prediction: p }: { prediction: PredictionRecord }) {
  const signalColor = { BUY: 'text-primary', HOLD: 'text-tertiary', SELL: 'text-error' }[p.signal]

  return (
    <div className="flex items-center gap-2 py-1.5 border-b border-outline-variant/8 last:border-0">
      {p.correct === null ? (
        <Clock size={12} className="text-on-surface-variant shrink-0" />
      ) : p.correct ? (
        <CheckCircle2 size={12} className="text-primary shrink-0" />
      ) : (
        <XCircle size={12} className="text-error shrink-0" />
      )}
      <span className="text-xs font-headline font-medium text-on-surface flex-1 truncate">{p.assetName}</span>
      <span className={cn('text-[10px] font-data font-bold', signalColor)}>{p.signal}</span>
      <span className="text-[10px] font-data text-on-surface-variant">{p.confidence}%</span>
      {p.correct !== null && (
        <span className={cn('text-[10px] font-headline', p.correct ? 'text-primary' : 'text-error')}>
          {p.correct ? 'WIN' : 'MISS'}
        </span>
      )}
      {p.correct === null && (
        <span className="text-[10px] font-headline text-on-surface-variant/60">PENDING</span>
      )}
    </div>
  )
}
