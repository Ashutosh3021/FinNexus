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

  // UI state
  isLoading: boolean
  simulateRefresh: () => void
}

export const useAppStore = create<AppState>((set, get) => ({
  // ─── Auth ────────────────────────────────────────────────────────────────────
  user: null,
  isAuthenticated: false,
  login: (user) => set({ user, isAuthenticated: true }),
  logout: () => set({ user: null, isAuthenticated: false }),

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
  submitAnswer: (questionId, answer) => {
    const question = get().hitlQuestions.find(q => q.id === questionId)
    if (!question) return
    const correct = question.type === 'MCQ'
      ? answer === question.correctAnswer
      : answer.trim().length > 20 // SAQ: length check as proxy
    const cashEarned = correct ? question.reward : Math.floor(question.reward * 0.3)

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
      return {
        hitlProgress: {
          ...state.hitlProgress,
          totalContributions: state.hitlProgress.totalContributions + 1,
          correctAnswers: state.hitlProgress.correctAnswers + (correct ? 1 : 0),
          cashEarned: state.hitlProgress.cashEarned + cashEarned,
          xp: state.hitlProgress.xp + (correct ? question.reward * 10 : 15),
          history: [newRecord, ...state.hitlProgress.history],
        },
        user: state.user
          ? { ...state.user, paperCash: state.user.paperCash + cashEarned }
          : state.user,
      }
    })
  },

  // ─── UI ──────────────────────────────────────────────────────────────────────
  isLoading: false,
  simulateRefresh: () => {
    set({ isLoading: true })
    setTimeout(() => {
      set({
        isLoading: false,
        lastPriceUpdate: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
      })
    }, 800)
  },
}))
