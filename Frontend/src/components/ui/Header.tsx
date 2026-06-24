// Legacy Header kept for backwards compatibility — main app uses AppLayout
import { Terminal } from "lucide-react"
import { cn } from "../../lib/utils"

const Header = ({ className }: { className?: string }) => {
  return (
    <header className={cn(
      "bg-background/80 backdrop-blur-xl font-headline tracking-tight sticky top-0 z-50 border-b border-outline-variant/15 w-full",
      className
    )}>
      <div className="max-w-7xl mx-auto px-6 py-3 flex justify-between items-center">
        <div className="flex items-center gap-3 text-primary">
          <Terminal className="w-6 h-6" />
          <span className="font-data font-bold tracking-tighter text-xl">FinNexus</span>
        </div>
      </div>
    </header>
  )
}

export { Header }
