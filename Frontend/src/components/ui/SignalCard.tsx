import { cn } from "../../lib/utils"
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "./Card"
import { ConfidenceRing } from "./ConfidenceRing"
import { ArrowUpRight, ArrowDownRight, Activity } from "lucide-react"

interface SignalCardProps {
  symbol: string
  name: string
  price: string
  change: string
  confidence: number
  variant?: 'invest' | 'hold' | 'skip'
  trend: 'Bullish' | 'Neutral' | 'Bearish'
  volume: string
  className?: string
}

const SignalCard = ({ symbol, name, price, change, confidence, variant = 'invest', trend, volume, className }: SignalCardProps) => {
  const isPositive = !change.startsWith('-')

  return (
    <Card className={cn("group hover:border-primary/30 transition-all", className)}>
      <CardHeader>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded bg-surface-container-lowest flex items-center justify-center border border-outline-variant/15 group-hover:bg-primary/5 transition-colors">
            <span className="font-data font-bold text-on-surface">{symbol}</span>
          </div>
          <div>
            <CardTitle>{name}</CardTitle>
            <p className="text-xs font-data text-on-surface-variant">{symbol}/USD</p>
          </div>
        </div>
        <div className={cn(
          "px-2.5 py-1 rounded font-headline text-xs font-bold tracking-wide border",
          variant === 'invest' ? "bg-primary/10 text-primary border-primary/20" : 
          variant === 'hold' ? "bg-tertiary/10 text-tertiary border-tertiary/20" : 
          "bg-error/10 text-error border-error/20"
        )}>
          {variant.toUpperCase()}
        </div>
      </CardHeader>

      <CardContent className="flex flex-col gap-6">
        <div className="flex justify-between items-center">
          <div>
            <p className="text-xs text-on-surface-variant mb-1 font-headline">Current Price</p>
            <p className="font-data text-2xl font-bold text-on-surface">{price}</p>
          </div>
          <ConfidenceRing value={confidence} variant={variant} size="sm" />
        </div>
        
        <div className="flex justify-between items-center">
          <div className="text-sm font-data text-on-surface-variant">Vol: {volume}</div>
          <div className={cn(
            "flex items-center gap-1 font-data text-sm font-medium",
            isPositive ? "text-primary" : "text-error"
          )}>
            {isPositive ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
            {change}
          </div>
        </div>
      </CardContent>

      <CardFooter className="flex justify-between items-center">
        <span className="text-sm text-on-surface-variant font-body">
          Trend: <span className={cn(
            "font-medium",
            trend === 'Bullish' ? "text-primary" : trend === 'Neutral' ? "text-tertiary" : "text-error"
          )}>{trend}</span>
        </span>
        <button className="text-xs font-headline font-semibold text-primary hover:text-primary-container transition-colors flex items-center gap-1">
          Analyze <Activity size={14} />
        </button>
      </CardFooter>
    </Card>
  )
}

export { SignalCard }
