import { useAppStore } from '../store/useAppStore'
import { cn } from '../lib/utils'
import { ExternalLink, Clock, Radio } from 'lucide-react'
import type { AssetClass, NewsItem } from '../types'

const CLASS_TABS: (AssetClass | 'All')[] = ['All', 'Stocks', 'Crypto', 'ETFs', 'Futures', 'Commodities']

const IMPACT_COLORS = {
  high:   'text-error bg-error/10 border-error/20',
  medium: 'text-tertiary bg-tertiary/10 border-tertiary/20',
  low:    'text-on-surface-variant bg-surface-container-high border-outline-variant/20',
}

const SENTIMENT_COLORS = {
  positive: 'text-primary',
  negative: 'text-error',
  neutral:  'text-on-surface-variant',
}

export function NewsPage() {
  const { news, newsFilter, setNewsFilter } = useAppStore()

  const filtered = newsFilter === 'All'
    ? news
    : news.filter(n => n.affectedClasses.includes(newsFilter as AssetClass))

  const highImpact = filtered.filter(n => n.impact === 'high')
  const rest = filtered.filter(n => n.impact !== 'high')

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="font-headline font-bold text-2xl text-on-surface">Global News Feed</h1>
          <p className="text-sm text-on-surface-variant mt-0.5">Real-time market-moving news with asset impact mapping</p>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <Radio size={12} className="text-primary animate-pulse" />
          <span className="text-xs font-headline text-primary">Live</span>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-hide">
        {CLASS_TABS.map((cls) => (
          <button
            key={cls}
            onClick={() => setNewsFilter(cls)}
            className={cn(
              'px-3 py-1.5 rounded-lg text-xs font-headline font-medium whitespace-nowrap transition-all border',
              newsFilter === cls
                ? 'bg-primary/10 text-primary border-primary/30'
                : 'border-outline-variant/20 text-on-surface-variant hover:text-on-surface'
            )}
          >
            {cls}
          </button>
        ))}
      </div>

      {/* High impact */}
      {highImpact.length > 0 && (
        <section>
          <div className="flex items-center gap-2 mb-3">
            <div className="w-2 h-2 rounded-full bg-error animate-pulse" />
            <h2 className="text-xs font-headline font-semibold text-error uppercase tracking-widest">High Impact</h2>
          </div>
          <div className="space-y-3">
            {highImpact.map(n => <NewsCard key={n.id} item={n} />)}
          </div>
        </section>
      )}

      {/* Rest */}
      {rest.length > 0 && (
        <section>
          <h2 className="text-xs font-headline font-semibold text-on-surface-variant/70 uppercase tracking-widest mb-3">Other News</h2>
          <div className="space-y-3">
            {rest.map(n => <NewsCard key={n.id} item={n} />)}
          </div>
        </section>
      )}

      {filtered.length === 0 && (
        <div className="py-16 text-center">
          <p className="text-on-surface-variant font-body text-sm">No news for this category right now.</p>
        </div>
      )}
    </div>
  )
}

function NewsCard({ item: n }: { item: NewsItem }) {
  const relativeTime = (ts: string) => {
    const diff = Math.floor((Date.now() - new Date(ts).getTime()) / 60000)
    if (diff < 60) return `${diff}m ago`
    const h = Math.floor(diff / 60)
    return `${h}h ago`
  }

  return (
    <article className={cn(
      'bg-surface-container-low rounded-xl border p-4 transition-all hover:border-opacity-50 group',
      n.impact === 'high' ? 'border-error/15 hover:border-error/30' :
      n.impact === 'medium' ? 'border-tertiary/15 hover:border-tertiary/30' :
      'border-outline-variant/15 hover:border-outline-variant/30'
    )}>
      <div className="flex items-start justify-between gap-3 mb-2">
        <h3 className="font-headline font-semibold text-sm text-on-surface leading-snug group-hover:text-primary transition-colors flex-1">
          {n.title}
        </h3>
        <a href={n.url} className="text-on-surface-variant hover:text-primary transition-colors shrink-0 mt-0.5">
          <ExternalLink size={13} />
        </a>
      </div>

      <p className="text-xs text-on-surface-variant font-body leading-relaxed mb-3">{n.summary}</p>

      <div className="flex flex-wrap items-center gap-2">
        {/* Impact */}
        <span className={cn('text-[10px] font-headline font-semibold px-2 py-0.5 rounded border', IMPACT_COLORS[n.impact])}>
          {n.impact.toUpperCase()} IMPACT
        </span>

        {/* Sentiment */}
        <span className={cn('text-[10px] font-headline font-semibold', SENTIMENT_COLORS[n.sentiment])}>
          {n.sentiment === 'positive' ? '↥' : n.sentiment === 'negative' ? '↧' : '–'}
          {' '}{n.sentiment}
        </span>

        {/* Affected asset classes */}
        {n.affectedClasses.map(cls => (
          <span key={cls} className="text-[10px] font-headline px-1.5 py-0.5 rounded bg-surface-container-high border border-outline-variant/15 text-on-surface-variant">
            {cls}
          </span>
        ))}

        <div className="ml-auto flex items-center gap-1.5 text-[10px] text-on-surface-variant font-data">
          <Clock size={9} />
          {relativeTime(n.publishedAt)} · {n.source}
        </div>
      </div>
    </article>
  )
}
