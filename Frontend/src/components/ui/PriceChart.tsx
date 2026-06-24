import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts'
import { cn } from "../../lib/utils"

interface PriceChartProps {
  data: { date: string, price: number }[]
  className?: string
  color?: string
}

const PriceChart = ({ data, className, color = "#10b981" }: PriceChartProps) => {
  return (
    <div className={cn("w-full h-[300px] bg-surface-container-highest/30 rounded-lg p-4 border border-outline-variant/15", className)}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.3}/>
              <stop offset="95%" stopColor={color} stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#86948a" opacity={0.1} />
          <XAxis 
            dataKey="date" 
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: '#bbcabf', fontSize: 12, fontFamily: 'Space Grotesk' }}
          />
          <YAxis 
            hide={true}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#111827', 
              borderColor: 'rgba(134, 148, 138, 0.15)', 
              borderRadius: '8px',
              fontFamily: 'Space Grotesk'
            }}
            itemStyle={{ color: '#dee1f7' }}
          />
          <Area 
            type="monotone" 
            dataKey="price" 
            stroke={color} 
            fillOpacity={1} 
            fill="url(#colorPrice)" 
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export { PriceChart }
