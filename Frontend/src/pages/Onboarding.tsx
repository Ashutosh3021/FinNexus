import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Bitcoin, Diamond, Sun, Layers, Landmark, Circle,
  ArrowRight, ArrowLeft, CheckCircle2, TrendingUp,
  BarChart2, Wheat, Building2,
} from 'lucide-react'
import { Button } from '../components/ui/Button'
import { cn } from '../lib/utils'
import { useAppStore } from '../store/useAppStore'
import * as api from '../lib/api'
import type { AssetClass } from '../types'

const STEPS = ['Assets', 'Markets', 'Experience', 'Goals', 'Review', 'Launch']

const allAssets = [
  { id: 'btc',      symbol: 'BTC',      name: 'Bitcoin',     icon: <Bitcoin size={18} /> },
  { id: 'eth',      symbol: 'ETH',      name: 'Ethereum',    icon: <Diamond size={18} /> },
  { id: 'sol',      symbol: 'SOL',      name: 'Solana',      icon: <Sun size={18} /> },
  { id: 'bnb',      symbol: 'BNB',      name: 'BNB',         icon: <Layers size={18} /> },
  { id: 'reliance', symbol: 'RELIANCE', name: 'Reliance',    icon: <Building2 size={18} /> },
  { id: 'nifty50',  symbol: 'NIFTY50',  name: 'Nifty 50',    icon: <BarChart2 size={18} /> },
  { id: 'gold',     symbol: 'GOLD',     name: 'Gold',        icon: <Landmark size={18} /> },
  { id: 'crude',    symbol: 'CRUDE',    name: 'Crude Oil',   icon: <Circle size={18} /> },
  { id: 'spy',      symbol: 'SPY',      name: 'S&P 500',     icon: <TrendingUp size={18} /> },
  { id: 'wheat',    symbol: 'WHEAT',    name: 'Wheat',       icon: <Wheat size={18} /> },
]

const assetClasses: AssetClass[] = ['Crypto', 'Stocks', 'ETFs', 'Futures', 'Commodities']

const experienceLevels = [
  { id: 'beginner',     label: 'Beginner',     desc: '< 1 year trading experience' },
  { id: 'intermediate', label: 'Intermediate', desc: '1–3 years, knows the basics' },
  { id: 'advanced',     label: 'Advanced',     desc: '3+ years, technical analysis' },
]

function ReviewRow({ label, value, highlight = false }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-outline-variant/10 last:border-0">
      <span className="text-on-surface-variant text-xs font-headline uppercase tracking-wider">{label}</span>
      <span className={cn('text-sm font-data font-medium', highlight ? 'text-primary' : 'text-on-surface')}>{value}</span>
    </div>
  )
}

export function Onboarding() {
  const navigate = useNavigate()
  const user = useAppStore((s) => s.user)
  const fetchHITLSession = useAppStore((s) => s.fetchHITLSession)
  const [step, setStep] = useState(0)
  const [selectedAssets, setSelectedAssets] = useState<string[]>(['btc', 'eth'])
  const [selectedClasses, setSelectedClasses] = useState<AssetClass[]>(['Crypto'])
  const [experience, setExperience] = useState('beginner')
  const [isLaunching, setIsLaunching] = useState(false)

  const toggleAsset = (id: string) =>
    setSelectedAssets(prev =>
      prev.includes(id) ? prev.filter(a => a !== id) : prev.length < 6 ? [...prev, id] : prev
    )

  const toggleClass = (cls: AssetClass) =>
    setSelectedClasses(prev =>
      prev.includes(cls) ? prev.filter(c => c !== cls) : [...prev, cls]
    )

  const canNext = () => {
    if (step === 0) return selectedAssets.length >= 1
    if (step === 1) return selectedClasses.length >= 1
    return true
  }

  return (
    <div className="bg-background text-on-surface min-h-screen flex flex-col items-center justify-center p-4">
      <main className="w-full max-w-2xl flex flex-col gap-6">
        {/* Progress dots */}
        <header className="flex flex-col items-center gap-3 text-center">
          <div className="flex gap-1.5">
            {STEPS.map((_, i) => (
              <div key={i} className={cn(
                'h-1.5 rounded-full transition-all duration-300',
                i < step ? 'bg-primary w-6' : i === step ? 'bg-primary w-10 shadow-[0_0_8px_#10b981]' : 'bg-surface-container-high w-6'
              )} />
            ))}
          </div>
          <p className="text-xs font-headline text-on-surface-variant uppercase tracking-wider">
            Step {step + 1} of {STEPS.length} — {STEPS[step]}
          </p>
        </header>

        {/* Card */}
        <section className="bg-surface-container-low rounded-xl p-6 sm:p-8 border border-outline-variant/20 min-h-[300px]">

          {step === 0 && (
            <>
              <h1 className="font-headline font-bold text-xl text-on-surface mb-1">Which assets do you want to track?</h1>
              <p className="text-sm text-on-surface-variant mb-5">Select 1–6 assets. You can change these later.</p>
              <div className="grid grid-cols-3 sm:grid-cols-5 gap-3">
                {allAssets.map((asset) => {
                  const sel = selectedAssets.includes(asset.id)
                  return (
                    <button
                      key={asset.id}
                      onClick={() => toggleAsset(asset.id)}
                      className={cn(
                        'relative p-3 rounded-xl flex flex-col items-center gap-2 border transition-all',
                        sel ? 'border-primary/50 bg-primary/5 shadow-[0_0_10px_rgba(16,185,129,0.1)]' : 'border-outline/20 hover:border-outline/40 bg-surface-container-high'
                      )}
                    >
                      {sel && <CheckCircle2 size={12} className="absolute top-2 right-2 text-primary" />}
                      <span className={cn('text-on-surface-variant', sel && 'text-primary')}>{asset.icon}</span>
                      <span className={cn('text-xs font-data font-bold', sel ? 'text-primary' : 'text-on-surface')}>{asset.symbol}</span>
                    </button>
                  )
                })}
              </div>
              <p className="text-xs text-on-surface-variant mt-3 text-center font-data">{selectedAssets.length} / 6 selected</p>
            </>
          )}

          {step === 1 && (
            <>
              <h1 className="font-headline font-bold text-xl text-on-surface mb-1">Which markets interest you?</h1>
              <p className="text-sm text-on-surface-variant mb-5">Select all that apply.</p>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {assetClasses.map((cls) => {
                  const sel = selectedClasses.includes(cls)
                  return (
                    <button
                      key={cls}
                      onClick={() => toggleClass(cls)}
                      className={cn(
                        'p-4 rounded-xl border text-left transition-all flex items-center gap-2',
                        sel ? 'border-primary/50 bg-primary/5 text-primary' : 'border-outline/20 text-on-surface-variant hover:border-outline/40'
                      )}
                    >
                      {sel && <CheckCircle2 size={14} className="shrink-0" />}
                      <span className="font-headline font-medium text-sm">{cls}</span>
                    </button>
                  )
                })}
              </div>
            </>
          )}

          {step === 2 && (
            <>
              <h1 className="font-headline font-bold text-xl text-on-surface mb-1">Your experience level?</h1>
              <p className="text-sm text-on-surface-variant mb-5">We'll adjust signal explanations and question difficulty.</p>
              <div className="space-y-3">
                {experienceLevels.map((lvl) => (
                  <button
                    key={lvl.id}
                    onClick={() => setExperience(lvl.id)}
                    className={cn(
                      'w-full p-4 rounded-xl border text-left transition-all flex justify-between items-center',
                      experience === lvl.id ? 'border-primary/50 bg-primary/5' : 'border-outline/20 hover:border-outline/40'
                    )}
                  >
                    <div>
                      <p className={cn('font-headline font-medium text-sm', experience === lvl.id ? 'text-primary' : 'text-on-surface')}>{lvl.label}</p>
                      <p className="text-xs text-on-surface-variant">{lvl.desc}</p>
                    </div>
                    {experience === lvl.id && <CheckCircle2 size={16} className="text-primary" />}
                  </button>
                ))}
              </div>
            </>
          )}

          {step === 3 && (
            <>
              <h1 className="font-headline font-bold text-xl text-on-surface mb-1">What are your goals?</h1>
              <p className="text-sm text-on-surface-variant mb-5">FinNexus works best when we know what you're optimising for.</p>
              <div className="space-y-2">
                {['Learn how markets work', 'Improve my trading accuracy', 'Paper trade before going live', 'Contribute analysis and earn rewards'].map((g) => (
                  <div key={g} className="flex items-center gap-3 p-3 bg-surface-container-high rounded-lg border border-outline/10 text-sm text-on-surface">
                    <CheckCircle2 size={14} className="text-primary shrink-0" />
                    {g}
                  </div>
                ))}
              </div>
            </>
          )}

          {step === 4 && (
            <>
              <h1 className="font-headline font-bold text-xl text-on-surface mb-5">
                Looking good, {user?.name?.split(' ')[0] ?? 'Trader'} 👋
              </h1>
              <div className="space-y-1">
                <ReviewRow label="Tracked Assets" value={selectedAssets.map(id => allAssets.find(a => a.id === id)?.symbol ?? id).join(', ')} />
                <ReviewRow label="Markets" value={selectedClasses.join(', ')} />
                <ReviewRow label="Experience" value={experienceLevels.find(l => l.id === experience)?.label ?? experience} />
                <ReviewRow label="Starting Paper Cash" value="₹100" highlight />
                <ReviewRow label="HITL Level" value="Level 1 — Beginner" />
              </div>
            </>
          )}

          {step === 5 && (
            <div className="flex flex-col items-center justify-center gap-4 py-8 text-center">
              <div className="w-16 h-16 rounded-full bg-primary/10 border border-primary/30 flex items-center justify-center shadow-[0_0_32px_rgba(16,185,129,0.2)]">
                <CheckCircle2 size={28} className="text-primary" />
              </div>
              <h1 className="font-headline font-bold text-2xl text-on-surface">You're all set!</h1>
              <p className="text-sm text-on-surface-variant max-w-xs">
                Your terminal is ready. ₹100 paper cash loaded. Answer questions to unlock more cash and climb the levels.
              </p>
            </div>
          )}
        </section>

        {/* Nav buttons */}
        <footer className="flex justify-between">
          <Button
            variant="outline"
            className="gap-2"
            onClick={() => step > 0 ? setStep(s => s - 1) : navigate('/')}
          >
            <ArrowLeft size={15} />
            {step === 0 ? 'Home' : 'Back'}
          </Button>

          {step < STEPS.length - 1 ? (
            <Button className="gap-2" disabled={!canNext()} onClick={() => setStep(s => s + 1)}>
              Continue <ArrowRight size={15} />
            </Button>
          ) : (
            <Button
              className="gap-2 px-8"
              disabled={isLaunching}
              onClick={async () => {
                setIsLaunching(true)
                try {
                  // Map experience to proficiency score for /assess endpoint
                  const proficiencyMap: Record<string, number> = {
                    beginner:     0.1,
                    intermediate: 0.4,
                    advanced:     0.7,
                  }
                  const proficiency = proficiencyMap[experience] ?? 0.1
                  const numericId = parseInt(
                    (user?.id ?? '1').replace(/\D/g, ''),
                    10,
                  ) || 1

                  // Call /assess to get recommended starting level
                  await api.assessStartingLevel(numericId, proficiency).catch(() => null)

                  // Pre-fetch first HITL session questions
                  await fetchHITLSession(1).catch(() => null)
                } finally {
                  setIsLaunching(false)
                  navigate('/app/prices')
                }
              }}
            >
              {isLaunching ? 'Launching…' : 'Launch Dashboard'} <ArrowRight size={15} />
            </Button>
          )}
        </footer>
      </main>
    </div>
  )
}
