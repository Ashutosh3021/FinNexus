import { cn } from "../../lib/utils"

interface PortfolioItem {
  asset: string
  symbol: string
  invested: string
  current: string
  pnl: string
}

const PortfolioTable = ({ items }: { items: PortfolioItem[] }) => {
  return (
    <div className="bg-surface-container-low rounded-lg overflow-hidden border border-outline-variant/15 shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-surface-container-highest/50">
              <th className="py-3 px-4 text-xs font-headline font-medium text-on-surface-variant uppercase tracking-wider">Asset</th>
              <th className="py-3 px-4 text-xs font-headline font-medium text-on-surface-variant uppercase tracking-wider text-right">Invested (INR)</th>
              <th className="py-3 px-4 text-xs font-headline font-medium text-on-surface-variant uppercase tracking-wider text-right">Current (INR)</th>
              <th className="py-3 px-4 text-xs font-headline font-medium text-on-surface-variant uppercase tracking-wider text-right">P&L</th>
            </tr>
          </thead>
          <tbody className="font-body text-sm divide-y divide-outline-variant/10">
            {items.map((item) => (
              <tr key={item.symbol} className="hover:bg-surface-container-highest/30 transition-colors">
                <td className="py-3 px-4 flex items-center gap-2">
                  <div className="w-8 h-8 rounded bg-surface-container-lowest border border-outline-variant/15 flex items-center justify-center text-xs font-bold font-data text-primary">
                    {item.symbol}
                  </div>
                  <span className="font-medium text-on-surface">{item.asset}</span>
                </td>
                <td className="py-3 px-4 text-right font-data text-on-surface-variant">{item.invested}</td>
                <td className="py-3 px-4 text-right font-data text-on-surface">{item.current}</td>
                <td className={cn(
                  "py-3 px-4 text-right font-data font-bold",
                  item.pnl.startsWith('+') ? "text-primary" : "text-error"
                )}>
                  {item.pnl}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export { PortfolioTable }
