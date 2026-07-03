import { create } from 'zustand'
import type {
  User, Asset, Prediction, PredictionRecord, MonthlyPerformance,
  PaperTrade, PaperPortfolio, NewsItem, HITLProgress, HITLQuestion,
  Timeframe, AssetClass,
} from '../types'
import {
  mockUser, mockAssets, mockPredictions, mockPredictionHistory,
  mockMonthlyPerformance, mockPaperTrades, mockNews,
  mockHITLProgress, hitlQuestions,
} from '../data/mockData'
import * as api from '../lib/api'

// ── SAQ scoring helper ────────────────────────────────────────────────────────
// Real scoring mirrors Bot/RAG/evaluator.py heuristic:
//   decision_quality, risk_awareness, synthesis keywords.
// SAQ is correct (score ≥ 0.5) when:
//   - length ≥ 30 chars (basic effort)
//   - contains at least one decision word AND one risk/synthesis word
const DECISION_WORDS = ['buy', 'sell', 'hold', 'short', 'long', 'enter', 'exit', 'reduce', 'hedge']
const RISK_WORDS     = ['stop', 'risk', 'loss', 'downside', 'protect', 'limit', 'drawdown', 'hedge', 'size']
const SYNTHESIS_WORDS = ['because', 'therefore', 'macro', 'rate', 'trend', 'momentum', 'volume', 'vix']

function scoreSAQ(answer: string): { correct: boolean; score: number } {
  const lower = answer.toLowerCase()
  const words = lower.split(/\s+/)
  const wordSet = new Set(words)

  if (answer.trim().length < 30) return { correct: false, score: 0.1 }

  const decisionHits = DECISION_WORDS.filter(w => wordSet.has(w) || lower.includes(w)).length
  const riskHits     = RISK_WORDS.filter(w => wordSet.has(w) || lower.includes(w)).length
  const synthHits    = SYNTHESIS_WORDS.filter(w => lower.includes(w)).length

  const dq = Math.min(decisionHits / 2, 1.0)
  const ra = Math.min(riskHits    / 2, 1.0)
  const sy = Math.min(synthHits   / 2, 1.0)
  const score = dq * 0.4 + ra * 0.35 + sy * 0.25
  return { correct: score >= 0.5, score }
}

// ── API integration flag ──────────────────────────────────────────────────────
// Set VITE_USE_API=true in .env to enable live backend calls.
// Defaults to mock data so the frontend works standalone.
const USE_API = import.meta.env.VITE_USE_API === 'true'

interface AppState {
  // Auth
  user: User | null
  isAuthenticated: boolean
  login: (user: User) => void
  logout: () => void

  // Assets / Prices
  assets: Asset[]
  selectedAssetClass: AssetClass | 'All'
  setAssetClass: (cls: AssetClass | 'All') => void
  selectedTimeframe: Timeframe
  setTimeframe: (tf: Timeframe) => void
  lastPriceUpdate: string

  // Predictions
  predictions: Prediction[]
  predictionHistory: PredictionRecord[]
  monthlyPerformance: MonthlyPerformance[]

  // Paper Trading
  portfolio: PaperPortfolio
  trades: PaperTrade[]
  executeTrade: (trade: Omit<PaperTrade, 'id' | 'timestamp' | 'resolvedAt' | 'analysis' | 'userResult' | 'botResult'>) => void

  // News
  news: NewsItem[]
  newsFilter: AssetClass | 'All'
  setNewsFilter: (cls: AssetClass | 'All') => void

  // HITL
  hitlProgress: HITLProgress
  hitlQuestions: HITLQuestion[]
  submitAnswer: (questionId: string, answer: string) => void
  advanceLevel: () => void

  // UI state
  isLoading: boolean
  apiError: string | null
  simulateRefresh: () => void
  refreshFromAPI: () => Promise<void>
}

export const useAppStore = create<AppState>((set, get) => ({
  // ─── Auth ────────────────────────────────────────────────────────────────────
  user: null,
  isAuthenticated: false,
  login: async (user) => {
    set({ user, isAuthenticated: true })
    // Authenticate with backend and fetch live stats if API mode enabled
    if (USE_API && user.id) {
      try {
        await api.login(user.id)
        const stats = await api.getUserStats(user.id)
        const cash  = await api.getPaperCash(user.id)
        set((state) => ({
          user: state.user
            ? {
                ...state.user,
                paperCash: cash.paper_cash,
                currentLevel: stats.current_level,
              }
            : state.user,
          hitlProgress: {
            ...state.hitlProgress,
            currentLevel: stats.current_level,
            cashEarned: cash.paper_cash,
            completedLevels: stats.completed_levels,
          },
        }))
      } catch (err) {
        console.warn('API login/stats failed — using mock data:', err)
      }
    }
  },
  logout: () => {
    api.clearToken()
    set({ user: null, isAuthenticated: false })
  },

  // ─── Assets ──────────────────────────────────────────────────────────────────
  assets: mockAssets,
  selectedAssetClass: 'All',
  setAssetClass: (cls) => set({ selectedAssetClass: cls }),
  selectedTimeframe: '1D',
  setTimeframe: (tf) => set({ selectedTimeframe: tf }),
  lastPriceUpdate: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),

  // ─── Predictions ─────────────────────────────────────────────────────────────
  predictions: mockPredictions,
  predictionHistory: mockPredictionHistory,
  monthlyPerformance: mockMonthlyPerformance,

  // ─── Paper Trading ────────────────────────────────────────────────────────────
  portfolio: {
    cash: mockUser.paperCash,
    trades: mockPaperTrades,
    holdings: {},
  },
  trades: mockPaperTrades,
  executeTrade: (tradeData) => {
    const newTrade: PaperTrade = {
      ...tradeData,
      id: `trade-${Date.now()}`,
      userResult: null,
      botResult: null,
      analysis: null,
      timestamp: new Date().toISOString(),
      resolvedAt: null,
    }
    set((state) => ({
      trades: [newTrade, ...state.trades],
      portfolio: {
        ...state.portfolio,
        cash: state.portfolio.cash - tradeData.amount,
        trades: [newTrade, ...state.portfolio.trades],
      },
    }))
  },

  // ─── News ─────────────────────────────────────────────────────────────────────
  news: mockNews,
  newsFilter: 'All',
  setNewsFilter: (cls) => set({ newsFilter: cls }),

  // ─── HITL ─────────────────────────────────────────────────────────────────────
  hitlProgress: mockHITLProgress,
  hitlQuestions: hitlQuestions,

  submitAnswer: async (questionId, answer) => {
    const question = get().hitlQuestions.find(q => q.id === questionId)
    if (!question) return

    // Local scoring
    let correct: boolean
    let cashEarned: number

    if (question.type === 'MCQ') {
      correct    = answer === question.correctAnswer
      cashEarned = correct ? question.reward : Math.floor(question.reward * 0.3)
    } else {
      // SAQ: use proper keyword-based scoring proxy
      const { correct: saqCorrect } = scoreSAQ(answer)
      correct    = saqCorrect
      cashEarned = correct ? question.reward : Math.floor(question.reward * 0.3)
    }

    // If API mode is on, submit to backend too (fire and forget)
    if (USE_API) {
      const userId = get().user?.id
      if (userId) {
        api.submitAnswer(userId, answer).catch((err) =>
          console.warn('API submitAnswer failed:', err),
        )
      }
    }

    set((state) => {
      const newRecord = {
        id: `h-${Date.now()}`,
        questionId,
        question: question.question,
        userAnswer: answer,
        correct,
        cashEarned,
        timestamp: new Date().toISOString(),
      }
      const newProgress = {
        ...state.hitlProgress,
        totalContributions: state.hitlProgress.totalContributions + 1,
        correctAnswers: state.hitlProgress.correctAnswers + (correct ? 1 : 0),
        cashEarned: state.hitlProgress.cashEarned + cashEarned,
        xp: state.hitlProgress.xp + (correct ? question.reward * 10 : 15),
        history: [newRecord, ...state.hitlProgress.history],
      }
      return {
        hitlProgress: newProgress,
        user: state.user
          ? { ...state.user, paperCash: state.user.paperCash + cashEarned }
          : state.user,
      }
    })
  },

  advanceLevel: () => {
    set((state) => {
      const currentLevel = state.hitlProgress.currentLevel
      const nextLevel    = currentLevel + 1
      const maxLevel     = 5 // levels 1-5 in mock data; Level 20 is special

      if (currentLevel >= maxLevel) {
        return {} // already at max local level
      }

      // Mark current level as completed
      const completedLevels = state.hitlProgress.completedLevels.includes(currentLevel)
        ? state.hitlProgress.completedLevels
        : [...state.hitlProgress.completedLevels, currentLevel]

      return {
        hitlProgress: {
          ...state.hitlProgress,
          currentLevel: nextLevel,
          completedLevels,
          // Reset XP toward next level threshold (keeps cumulative total)
        },
        user: state.user
          ? { ...state.user, currentLevel: nextLevel }
          : state.user,
      }
    })
  },

  // ─── UI ──────────────────────────────────────────────────────────────────────
  isLoading: false,
  apiError: null,

  simulateRefresh: () => {
    set({ isLoading: true })
    setTimeout(() => {
      set({
        isLoading: false,
        lastPriceUpdate: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
      })
    }, 800)
  },

  refreshFromAPI: async () => {
    if (!USE_API) {
      get().simulateRefresh()
      return
    }
    const userId = get().user?.id
    if (!userId) return
    set({ isLoading: true, apiError: null })
    try {
      const [stats, cash] = await Promise.all([
        api.getUserStats(userId),
        api.getPaperCash(userId),
      ])
      set((state) => ({
        isLoading: false,
        lastPriceUpdate: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
        user: state.user
          ? {
              ...state.user,
              paperCash: cash.paper_cash,
              currentLevel: stats.current_level,
            }
          : state.user,
        hitlProgress: {
          ...state.hitlProgress,
          currentLevel: stats.current_level,
          cashEarned: cash.paper_cash,
          completedLevels: stats.completed_levels,
        },
      }))
    } catch (err) {
      set({
        isLoading: false,
        apiError: err instanceof Error ? err.message : 'API error',
      })
    }
  },
}))
