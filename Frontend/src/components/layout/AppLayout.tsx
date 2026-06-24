import { useState } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import {
  Terminal, BarChart2, TrendingUp, Brain, Shield,
  Swords, Newspaper, Users, LogOut, Menu, X, RefreshCw,
  ChevronRight,
} from 'lucide-react'
import { cn } from '../../lib/utils'
import { useAppStore } from '../../store/useAppStore'

const navItems = [
  { to: '/app/prices',      icon: BarChart2,   label: 'Live Prices',    badge: 'F1' },
  { to: '/app/trends',      icon: TrendingUp,  label: 'Recent Trends',  badge: 'F2' },
  { to: '/app/predictions', icon: Brain,       label: 'Predictions',    badge: 'F3' },
  { to: '/app/confidence',  icon: Shield,      label: 'Confidence',     badge: 'F4' },
  { to: '/app/trading',     icon: Swords,      label: 'Paper Trading',  badge: 'F5' },
  { to: '/app/news',        icon: Newspaper,   label: 'News Feed',      badge: 'F6' },
  { to: '/app/contribute',  icon: Users,       label: 'Contribute',     badge: 'F7' },
]

export function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { user, logout, simulateRefresh, isLoading, lastPriceUpdate } = useAppStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <div className="h-screen bg-background flex overflow-hidden">
      {/* ── Mobile Overlay ─────────────────────────────────── */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-30 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* ── Sidebar ────────────────────────────────────────── */}
      <aside
        className={cn(
          'fixed top-0 left-0 h-screen w-64 bg-surface-container-low border-r border-outline-variant/15 z-40 flex flex-col transition-transform duration-200',
          'md:static md:translate-x-0 md:shrink-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Logo */}
        <div className="px-5 py-4 border-b border-outline-variant/15 flex items-center justify-between">
          <div className="flex items-center gap-2.5 text-primary">
            <Terminal className="w-5 h-5" />
            <span className="font-data font-bold text-lg tracking-tighter">FinNexus</span>
          </div>
          <button
            className="md:hidden text-on-surface-variant hover:text-on-surface"
            onClick={() => setSidebarOpen(false)}
          >
            <X size={18} />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 px-3 space-y-0.5 overflow-y-auto">
          {navItems.map(({ to, icon: Icon, label, badge }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-headline font-medium transition-all group',
                  isActive
                    ? 'bg-primary/10 text-primary'
                    : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
                )
              }
            >
              {({ isActive }) => (
                <>
                  <Icon size={16} className={cn(isActive ? 'text-primary' : 'text-on-surface-variant group-hover:text-on-surface')} />
                  <span className="flex-1">{label}</span>
                  <span className={cn(
                    'text-[10px] font-data px-1.5 py-0.5 rounded border',
                    isActive
                      ? 'border-primary/30 text-primary bg-primary/5'
                      : 'border-outline-variant/20 text-on-surface-variant/50'
                  )}>
                    {badge}
                  </span>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Bottom user area */}
        <div className="border-t border-outline-variant/15 p-3 space-y-2">
          {/* Cash balance */}
          <div className="flex items-center justify-between px-3 py-2 bg-surface-container-high rounded-lg border border-outline-variant/15">
            <div>
              <p className="text-[10px] font-headline text-on-surface-variant uppercase tracking-wider">Paper Cash</p>
              <p className="font-data font-bold text-primary text-base">₹{user?.paperCash ?? 100}</p>
            </div>
            <ChevronRight size={14} className="text-on-surface-variant" />
          </div>

          {/* User info */}
          {user && (
            <div className="flex items-center gap-3 px-3 py-2">
              <div className="w-8 h-8 rounded bg-primary/20 border border-primary/30 flex items-center justify-center text-primary font-data font-bold text-xs">
                {user.avatar}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-headline font-medium text-on-surface truncate">{user.name}</p>
                <p className="text-[10px] text-on-surface-variant truncate">{user.email}</p>
              </div>
              <button
                onClick={handleLogout}
                className="text-on-surface-variant hover:text-error transition-colors"
                title="Logout"
              >
                <LogOut size={14} />
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* ── Main Content ───────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden h-screen">
        {/* Top bar */}
        <header className="sticky top-0 z-20 bg-background/80 backdrop-blur-xl border-b border-outline-variant/15 px-4 py-3 flex items-center justify-between">
          <button
            className="md:hidden text-on-surface-variant hover:text-on-surface transition-colors"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu size={20} />
          </button>

          <div className="flex items-center gap-3 ml-auto">
            {/* Live status */}
            <div className="hidden sm:flex items-center gap-2 text-xs text-on-surface-variant font-headline">
              <span>Updated {lastPriceUpdate}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse shadow-[0_0_6px_rgba(16,185,129,0.5)]" />
              <span className="text-xs font-headline text-primary">Live</span>
            </div>
            <button
              onClick={simulateRefresh}
              disabled={isLoading}
              className="p-1.5 rounded hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface transition-colors disabled:opacity-50"
              title="Refresh prices"
            >
              <RefreshCw size={14} className={cn(isLoading && 'animate-spin')} />
            </button>
            {/* Mobile cash balance */}
            <div className="sm:hidden flex items-center gap-1.5 bg-surface-container-high rounded px-2.5 py-1 border border-outline-variant/15">
              <span className="text-xs font-data font-bold text-primary">₹{user?.paperCash ?? 100}</span>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
