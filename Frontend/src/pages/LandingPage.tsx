import { useNavigate } from 'react-router-dom'
import { Terminal, Activity, Zap, ShieldCheck, BarChart2, Users } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { useAppStore } from '../store/useAppStore'
import { mockUser } from '../data/mockData'

export function LandingPage() {
  const navigate = useNavigate()
  const login = useAppStore((s) => s.login)

  const handleGoogleLogin = () => {
    // Simulate Google OAuth — in prod this calls your OAuth provider
    login(mockUser)
    navigate('/onboarding')
  }

  const features = [
    { icon: BarChart2, title: 'Real-Time Prices', desc: 'Live prices across Stocks, Crypto, ETFs, Futures & Commodities.' },
    { icon: Activity, title: 'Trend Signals', desc: 'Visual Bullish / Bearish / Neutral signals with 1D, 1W, 1M timeframes.' },
    { icon: Zap, title: 'ML Predictions', desc: 'Combined ML + RAG + Bot signals with confidence scores.' },
    { icon: ShieldCheck, title: 'Confidence Tracker', desc: 'Monitor prediction accuracy against real market data.' },
    { icon: BarChart2, title: 'Paper Trading', desc: 'Practice with ₹100 paper cash. Compare your calls vs the bot.' },
    { icon: Users, title: 'Contribute & Earn', desc: 'Answer market questions, level up, and earn more paper cash.' },
  ]

  return (
    <div className="bg-background text-on-surface min-h-screen flex flex-col relative overflow-hidden">
      {/* Mesh grid */}
      <div
        className="absolute inset-0 pointer-events-none opacity-30"
        style={{
          backgroundImage: 'linear-gradient(to right, rgba(134,148,138,0.07) 1px, transparent 1px), linear-gradient(to bottom, rgba(134,148,138,0.07) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />

      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-xl border-b border-outline-variant/10 px-6 py-3 flex justify-between items-center">
        <div className="flex items-center gap-2.5 text-primary">
          <Terminal className="w-5 h-5" />
          <span className="font-data font-bold tracking-tighter text-lg">FinNexus</span>
        </div>
        <Button variant="outline" size="sm" onClick={handleGoogleLogin}>
          Log In
        </Button>
      </header>

      <main className="flex-grow pt-28 pb-24 px-4 md:px-8 max-w-5xl mx-auto w-full flex flex-col gap-20 z-10">
        {/* Hero */}
        <section className="flex flex-col items-center text-center gap-6 mt-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded bg-surface-container border border-outline-variant/15 text-xs font-label text-on-surface-variant">
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse shadow-[0_0_6px_#10b981]" />
            Market Intelligence Active
          </div>

          <h1 className="text-4xl md:text-6xl font-headline font-bold tracking-tight leading-tight">
            Stop Guessing.<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-primary-container">
              Start Investing Smart.
            </span>
          </h1>

          <p className="text-base md:text-lg text-on-surface-variant max-w-xl font-body">
            FinNexus combines ML predictions, real-time data, and human intelligence
            to give you institutional-grade trading signals in a clean terminal.
          </p>

          <Button size="lg" className="gap-3 mt-2" onClick={handleGoogleLogin}>
            <svg viewBox="0 0 24 24" className="w-5 h-5" aria-hidden="true">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Get Started Free — Google Sign In
          </Button>
        </section>

        {/* Features grid */}
        <section>
          <h2 className="text-center text-xs font-label uppercase tracking-widest text-on-surface-variant mb-8">
            7 Intelligence Modules
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {features.map(({ icon: Icon, title, desc }, i) => (
              <div
                key={i}
                className="bg-surface-container-low rounded-xl p-5 border border-outline-variant/15 hover:border-primary/20 transition-all hover:shadow-[0_0_20px_rgba(16,185,129,0.05)] group"
              >
                <div className="w-9 h-9 rounded bg-primary/10 border border-primary/20 flex items-center justify-center text-primary mb-3 group-hover:shadow-[0_0_12px_rgba(16,185,129,0.15)] transition-all">
                  <Icon size={16} />
                </div>
                <h3 className="font-headline font-semibold text-on-surface text-sm mb-1">{title}</h3>
                <p className="text-xs text-on-surface-variant font-body">{desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="bg-surface-container-low rounded-xl p-8 border border-outline-variant/15 text-center flex flex-col items-center gap-4">
          <h2 className="font-headline font-bold text-2xl text-on-surface">Ready to trade smarter?</h2>
          <p className="text-on-surface-variant text-sm max-w-md">
            Start with ₹100 paper cash. No real money at risk. Learn, earn, and level up.
          </p>
          <Button size="lg" onClick={handleGoogleLogin} className="gap-2">
            Start for Free
          </Button>
        </section>
      </main>

      <footer className="z-10 py-6 border-t border-outline-variant/10 text-center text-xs text-on-surface-variant font-body">
        © 2026 FinNexus · Trading Intelligence Platform · For educational purposes only
      </footer>
    </div>
  )
}
