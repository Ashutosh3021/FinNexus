import { cn } from "../../lib/utils"

interface ConfidenceRingProps {
  value: number
  variant?: 'invest' | 'hold' | 'skip'
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const ConfidenceRing = ({ value, variant = 'invest', size = 'md', className }: ConfidenceRingProps) => {
  const radius = 45
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (value / 100) * circumference

  const variants = {
    invest: "text-primary drop-shadow-[0_0_8px_rgba(16,185,129,0.3)]",
    hold: "text-tertiary drop-shadow-[0_0_8px_rgba(255,185,95,0.3)]",
    skip: "text-error drop-shadow-[0_0_8px_rgba(255,180,171,0.3)]",
  }

  const sizes = {
    sm: "w-12 h-12",
    md: "w-32 h-32",
    lg: "w-48 h-48",
  }

  const textSizes = {
    sm: "text-[10px]",
    md: "text-3xl",
    lg: "text-5xl",
  }

  const labelSizes = {
    sm: "text-[6px]",
    md: "text-xs",
    lg: "text-sm",
  }

  const labels = {
    invest: "Invest",
    hold: "Hold",
    skip: "Skip",
  }

  return (
    <div className={cn("relative flex items-center justify-center", sizes[size], className)}>
      <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
        <circle
          className="text-surface-container-lowest"
          cx="50"
          cy="50"
          fill="none"
          r={radius}
          stroke="currentColor"
          strokeWidth="8"
        />
        <circle
          className={cn("transition-all duration-500 ease-out", variants[variant])}
          cx="50"
          cy="50"
          fill="none"
          r={radius}
          stroke="currentColor"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          strokeWidth="8"
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className={cn("font-label uppercase tracking-widest", variants[variant], labelSizes[size])}>
          {labels[variant]}
        </span>
        <span className={cn("font-data font-bold text-on-surface", textSizes[size])}>
          {value}%
        </span>
      </div>
    </div>
  )
}

export { ConfidenceRing }
