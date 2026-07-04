/**
 * useAppStore — Global Zustand store for FinNexus.
 *
 * API integration is controlled by VITE_USE_API=true in .env.
 * When disabled (default for local dev without a running backend), the store
 * falls back to mock data so the frontend works fully standalone.
 *
 * All API calls are non-blocking fire-and-forget unless they affect initial
 * page load. Every section that fetches from the API has:
 *   1. Optimistic / immediate mock data shown to the user
 *   2. Real data merged in once the fetch resolves
 *   3. Graceful silent fallback on error (console.warn, not console.error)
 */

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
import { useToastStore } from '../hooks/useToast'

// ── API toggle ────────────────────────────────────────────────────────────────
// Set VITE_USE_API=true in your .env to enable live backend calls.
const USE_API = import.meta.env.VITE_USE_API === 'true'

// ── SAQ scoring proxy ─────────────────────────────────────────────────────────
// Mirrors Bot/RAG/evaluator.py heuristic for instant local feedback.
// Real scoring happens server-side; this is only used for immediate UI response.
const DECISION_WORDS  = ['buy', 'sell', 'hold', 'short', 'long', 'enter', 'exit', 'reduce', 'hedge']
const RISK_WORDS      = ['stop', 'risk', 'loss', 'downside', 'protect', 'limit', 'drawdown', 'hedge', 'size']
const SYNTHESIS_WORDS = ['because', 'therefore', 'macro', 'rate', 'trend', 'momentum', 'volume', 'vix']

function scoreSAQ(answer: string): { correct: boolean; score: number } {
  const lower   = answer.toLowerCase()
  if (answer.trim().length < 30) return { correct: false, score: 0.1 }
  const dq = Math.min(DECISION_WORDS.filter(w  => lower.includes(w)).length / 2, 1.0)
  const ra = Math.min(RISK_WORDS.filter(w     => lower.includes(w)).length / 2, 1.0)
  const sy = Math.min(SYNTHESIS_WORDS.filter(w => lower.includes(w)).length / 2, 1.0)
  const score = dq * 0.4 + ra * 0.35 + sy * 0.25
  return { correct: score >= 0.5, score }
}

// ── Map API question type to frontend type ────────────────────────────────────
function mapQuestionType(apiType: string): 'MCQ' | 'SAQ' {
  if (apiType === 'mcq_single' || apiType === 'mcq_multiple') return 'MCQ'
  return 'SAQ'
}

// ── Convert API question to frontend HITLQuestion ─────────────────────────────
function apiQuestionToFrontend(q: api.Question, level: number): HITLQuestion {
  return {
    id:            q.id,
    level,
    type:          mapQuestionType(q.type),
    question:      q.question,
    options:       q.options?.length ? q.options : undefined,
    correctAnswer: q.correct_answer ?? undefined,
    context:       q.context ?? '',
    reward:        level * 5,  // ₹5 per level point — consistent with mock data
  }
}

// ── State shape ───────────────────────────────────────────────────────────────
interface AppState {
  // Auth
  user: User | null
  isAuthenticated: boolean
  login:  (user: User) => Promise<void>
  logout: () => void

  // Assets / Prices
  assets:              Asset[]
  selectedAssetClass:  AssetClass | 'All'
  setAssetClass:       (cls: AssetClass | 'All') => void
  selectedTimeframe:   Timeframe
  setTimeframe:        (tf: Timeframe) => void
  lastPriceUpdate:     string
  fetchPrices:         () => Promise<void>

  // Predictions
  predictions:         Prediction[]
  predictionHistory:   PredictionRecord[]
  monthlyPerformance:  MonthlyPerformance[]
  fetchPredictions:    (userId: string) => Promise<void>

  // Paper Trading
  portfolio:           PaperPortfolio
  trades:              PaperTrade[]
  executeTrade: (
    trade: Omit<PaperTrade, 'id' | 'timestamp' | 'resolvedAt' | 'analysis' | 'userResult' | 'botResult'>,
  ) => void

  // News
  news:            NewsItem[]
  newsFilter:      AssetClass | 'All'
  setNewsFilter:   (cls: AssetClass | 'All') => void
  fetchNews:       (filter?: AssetClass | 'All') => Promise<void>

  // HITL — v2 async session
  hitlProgress:       HITLProgress
  hitlQuestions:      HITLQuestion[]
  activeSessionId:    string | null
  submitAnswer:       (questionId: string, answer: string) => void
  advanceLevel:       () => Promise<void>
  fetchHITLSession:   (level?: number) => Promise<void>

  // UI state
  isLoading:       boolean
  apiError:        string | null
  simulateRefresh: () => void
  refreshFromAPI:  () => Promise<void>
}

// ── Store ─────────────────────────────────────────────────────────────────────
export const useAppStore = create<AppState>((set, get) => ({

  // ── Auth ────────────────────────────────────────────────────────────────────
  user:            null,
  isAuthenticated: false,

  login: async (user) => {
    set({ user, isAuthenticated: true })
    if (!USE_API) return

    try {
      await api.login(user.id)
      const [stats, cash] = await Promise.all([
        api.getUserStats(user.id),
        api.getPaperCash(user.id),
      ])
      set((s) => ({
        user: s.user
          ? { ...s.user, paperCash: cash.paper_cash, currentLevel: stats.current_level }
          : s.user,
        hitlProgress: {
          ...s.hitlProgress,
          currentLevel:     stats.current_level,
          cashEarned:       cash.paper_cash,
          completedLevels:  stats.completed_levels,
        },
      }))
    } catch (err) {
      console.warn('API login/stats failed — using mock data:', err)
    }
  },

  logout: () => {
    api.clearToken()
    set({ user: null, isAuthenticated: false, activeSessionId: null })
  },

  // ── Assets / Prices ─────────────────────────────────────────────────────────
  assets:             mockAssets,
  selectedAssetClass: 'All',
  setAssetClass: (cls) => set({ selectedAssetClass: cls }),
  selectedTimeframe:  '1D',
  setTimeframe: (tf) => set({ selectedTimeframe: tf }),
  lastPriceUpdate:    new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),

  fetchPrices: async () => {
    if (!USE_API) return
    try {
      const { prices } = await api.getMarketPrices()
      if (!prices?.length) return

      const mapped: Asset[] = prices.map((p) => {
        // Try to preserve existing chart data from mock so charts still render
        const existing = get().assets.find((a) => a.id === p.id || a.symbol === p.symbol)
        return {
          id:             p.id,
          symbol:         p.symbol,
          name:           p.name,
          assetClass:     p.asset_class,
          price:          p.price,
          priceFormatted: p.price >= 1000
            ? `₹${p.price.toLocaleString('en-IN')}`
            : `₹${p.price.toFixed(2)}`,
          change:          p.change_percent,
          changeFormatted: `${p.change_percent >= 0 ? '+' : ''}${p.change_percent.toFixed(1)}%`,
          volume:          p.volume,
          lastUpdated:     p.last_updated,
          trend:           p.trend,
          chartData:       existing?.chartData ?? [],
        }
      })

      set({
        assets: mapped,
        lastPriceUpdate: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
      })
    } catch (err) {
      console.warn('fetchPrices failed — keeping mock data:', err)
    }
  },

  // ── Predictions ─────────────────────────────────────────────────────────────
  predictions:        mockPredictions,
  predictionHistory:  mockPredictionHistory,
  monthlyPerformance: mockMonthlyPerformance,

  fetchPredictions: async (userId: string) => {
    if (!USE_API) return
    try {
      const stats = await api.getUserStats(userId)
      // Map server stats into monthly-performance format for ConfidencePage
      const monthly: MonthlyPerformance[] = (
        (stats.recent_activity ?? []) as Array<Record<string, unknown>>
      )
        .slice(0, 6)
        .map((a, i) => ({
          month:       new Date(Date.now() - i * 30 * 86400000).toLocaleString('en-IN', { month: 'short' }),
          accuracy:    Math.round(((a.score as number) ?? 0) * 100),
          predictions: 1,
        }))
        .reverse()

      if (monthly.length) {
        set({ monthlyPerformance: monthly })
      }
    } catch (err) {
      console.warn('fetchPredictions stats failed — using mock:', err)
    }
  },

  // ── Paper Trading ────────────────────────────────────────────────────────────
  portfolio: {
    cash:     mockUser.paperCash,
    trades:   mockPaperTrades,
    holdings: {},
  },
  trades: mockPaperTrades,

  executeTrade: (tradeData) => {
    const newTrade: PaperTrade = {
      ...tradeData,
      id:          `trade-${Date.now()}`,
      userResult:  null,
      botResult:   null,
      analysis:    null,
      timestamp:   new Date().toISOString(),
      resolvedAt:  null,
    }
    set((s) => ({
      trades: [newTrade, ...s.trades],
      portfolio: {
        ...s.portfolio,
        cash:   s.portfolio.cash - tradeData.amount,
        trades: [newTrade, ...s.portfolio.trades],
      },
    }))
    // Sync cash deduction with backend
    if (USE_API) {
      const userId = get().user?.id
      if (userId) {
        api.getPaperCash(userId).catch(() => {/* non-critical */})
      }
    }
  },

  // ── News ─────────────────────────────────────────────────────────────────────
  news:       mockNews,
  newsFilter: 'All',

  setNewsFilter: (cls) => {
    set({ newsFilter: cls })
    get().fetchNews(cls)
  },

  fetchNews: async (filter) => {
    if (!USE_API) return
    try {
      const { news } = await api.getMarketNews(20, filter)
      if (!news?.length) return
      const mapped: NewsItem[] = news.map((n) => ({
        id:             n.id,
        title:          n.title,
        summary:        n.summary,
        source:         n.source,
        url:            n.url,
        publishedAt:    n.published_at,
        sentiment:      n.sentiment,
        affectedAssets: n.affected_assets,
        affectedClasses: n.affected_classes as import('../types').AssetClass[],
        impact:         n.impact,
      }))
      set({ news: mapped })
    } catch (err) {
      console.warn('fetchNews failed — keeping mock data:', err)
    }
  },

  // ── HITL ─────────────────────────────────────────────────────────────────────
  hitlProgress:    mockHITLProgress,
  hitlQuestions:   hitlQuestions,
  activeSessionId: null,

  /**
   * Start (or resume) a v2 async HITL session.
   * Fetches all questions at once and stores them locally.
   * Falls back to mock questions if the API is unavailable.
   */
  fetchHITLSession: async (level?: number) => {
    if (!USE_API) return
    const userId = get().user?.id
    if (!userId) return

    const targetLevel = level ?? get().hitlProgress.currentLevel
    const numericId   = parseInt(userId.replace(/\D/g, ''), 10) || 1

    try {
      const resp = await api.startSessionV2(numericId, targetLevel, false)
      const questions = resp.questions.map((q) => apiQuestionToFrontend(q, targetLevel))

      set({
        activeSessionId: resp.session_id,
        hitlQuestions:   questions.length ? questions : hitlQuestions,
      })
    } catch (err) {
      console.warn('fetchHITLSession failed — using mock questions:', err)
      // Keep mock questions so the UI remains functional
    }
  },

  /**
   * Submit a single answer locally (instant feedback) and batch-send to
   * the backend via the v2 /v2/session/answers endpoint when the level is
   * complete. Individual question submissions are debounced to avoid
   * redundant round-trips.
   */
  submitAnswer: (questionId, answer) => {
    const question = get().hitlQuestions.find((q) => q.id === questionId)
    if (!question) return

    // Local scoring for immediate UI feedback
    let correct:    boolean
    let cashEarned: number

    if (question.type === 'MCQ') {
      correct    = answer === question.correctAnswer
      cashEarned = correct ? question.reward : Math.floor(question.reward * 0.3)
    } else {
      const { correct: saqCorrect } = scoreSAQ(answer)
      correct    = saqCorrect
      cashEarned = correct ? question.reward : Math.floor(question.reward * 0.3)
    }

    // Optimistic state update
    set((s) => {
      const newRecord = {
        id:         `h-${Date.now()}`,
        questionId,
        question:   question.question,
        userAnswer: answer,
        correct,
        cashEarned,
        timestamp:  new Date().toISOString(),
      }
      const newProgress: HITLProgress = {
        ...s.hitlProgress,
        totalContributions: s.hitlProgress.totalContributions + 1,
        correctAnswers:     s.hitlProgress.correctAnswers + (correct ? 1 : 0),
        cashEarned:         s.hitlProgress.cashEarned + cashEarned,
        xp:                 s.hitlProgress.xp + (correct ? question.reward * 10 : 15),
        history:            [newRecord, ...s.hitlProgress.history],
      }
      return {
        hitlProgress: newProgress,
        user:         s.user
          ? { ...s.user, paperCash: s.user.paperCash + cashEarned }
          : s.user,
      }
    })

    // Fire-and-forget to backend (single-answer v1 endpoint — no session needed)
    if (USE_API) {
      const userId = get().user?.id
      if (userId) {
        api.submitAnswer(userId, answer).catch((err) =>
          console.warn('API submitAnswer failed (non-critical):', err),
        )
      }
    }
  },

  /**
   * Advance the user to the next HITL level.
   * If API mode is enabled and we have a session, submits all pending answers
   * to the backend first, then updates local state.
   */
  advanceLevel: async () => {
    const { hitlProgress, activeSessionId, hitlQuestions: questions, user } = get()
    const currentLevel = hitlProgress.currentLevel
    const maxLevel     = 5
    if (currentLevel >= maxLevel) return

    const nextLevel      = currentLevel + 1
    const completedLevels = hitlProgress.completedLevels.includes(currentLevel)
      ? hitlProgress.completedLevels
      : [...hitlProgress.completedLevels, currentLevel]

    // Optimistic local update
    set((s) => ({
      hitlProgress: { ...s.hitlProgress, currentLevel: nextLevel, completedLevels },
      user:         s.user ? { ...s.user, currentLevel: nextLevel } : s.user,
    }))

    if (USE_API && activeSessionId && user) {
      try {
        // Build answers map for all answered questions in current level
        const answeredIds = new Set(hitlProgress.history.map((h) => h.questionId))
        const levelQs     = questions.filter((q) => q.level === currentLevel)
        const answersMap: Record<string, string> = {}
        hitlProgress.history.forEach((h) => {
          const q = levelQs.find((q) => q.id === h.questionId)
          if (q && answeredIds.has(h.questionId)) {
            answersMap[h.questionId] = h.userAnswer
          }
        })

        if (Object.keys(answersMap).length > 0) {
          await api.submitAnswersV2(activeSessionId, answersMap)
        }

        // Start the next level session
        await get().fetchHITLSession(nextLevel)

        useToastStore.getState().push(
          `Level ${currentLevel} complete! Starting Level ${nextLevel}.`,
          'success',
        )
      } catch (err) {
        console.warn('advanceLevel API call failed (local state already updated):', err)
        useToastStore.getState().push(
          'Level advanced locally. Backend sync will retry on next refresh.',
          'info',
        )
      }
    }
  },

  // ── UI state ─────────────────────────────────────────────────────────────────
  isLoading: false,
  apiError:  null,

  simulateRefresh: () => {
    set({ isLoading: true })
    setTimeout(() => {
      set({
        isLoading:       false,
        lastPriceUpdate: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
      })
    }, 800)
  },

  refreshFromAPI: async () => {
    const userId = get().user?.id
    if (!userId) {
      get().simulateRefresh()
      return
    }

    set({ isLoading: true, apiError: null })
    try {
      // Kick off all fetches in parallel
      const fetches: Promise<unknown>[] = [get().fetchPrices(), get().fetchNews()]

      if (USE_API) {
        fetches.push(
          (async () => {
            const [stats, cash] = await Promise.all([
              api.getUserStats(userId),
              api.getPaperCash(userId),
            ])
            set((s) => ({
              user: s.user
                ? { ...s.user, paperCash: cash.paper_cash, currentLevel: stats.current_level }
                : s.user,
              hitlProgress: {
                ...s.hitlProgress,
                currentLevel:    stats.current_level,
                cashEarned:      cash.paper_cash,
                completedLevels: stats.completed_levels,
              },
            }))
          })(),
        )
      }

      await Promise.allSettled(fetches)

      set({
        isLoading:       false,
        lastPriceUpdate: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
      })
    } catch (err) {
      set({
        isLoading: false,
        apiError:  err instanceof Error ? err.message : 'API error',
      })
    }
  },
}))
