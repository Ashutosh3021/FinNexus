// ─── Asset Classes ────────────────────────────────────────────────────────────
export type AssetClass = 'Stocks' | 'Crypto' | 'ETFs' | 'Futures' | 'Commodities'

export type TrendSignal = 'Bullish' | 'Bearish' | 'Neutral'
export type PredictionSignal = 'BUY' | 'HOLD' | 'SELL'
export type Timeframe = '1D' | '1W' | '1M'

// ─── Price Data ───────────────────────────────────────────────────────────────
export interface Asset {
  id: string
  symbol: string
  name: string
  assetClass: AssetClass
  price: number
  priceFormatted: string
  change: number          // percentage
  changeFormatted: string
  volume: string
  lastUpdated: string
  trend: TrendSignal
  chartData: ChartPoint[]
}

export interface ChartPoint {
  date: string
  price: number
  open?: number
  high?: number
  low?: number
  close?: number
  volume?: number
}

// ─── Predictions ──────────────────────────────────────────────────────────────
export interface Prediction {
  assetId: string
  signal: PredictionSignal
  confidence: number       // 0-100
  modelPerformance: number // 0-100
  reasoning: string
  mlSignal: PredictionSignal
  ragSignal: PredictionSignal
  botSignal: PredictionSignal
  timestamp: string
}

// ─── Confidence Dashboard ─────────────────────────────────────────────────────
export interface PredictionRecord {
  id: string
  assetId: string
  assetName: string
  signal: PredictionSignal
  confidence: number
  actual: PredictionSignal | null
  correct: boolean | null
  date: string
}

export interface MonthlyPerformance {
  month: string
  accuracy: number
  predictions: number
}

// ─── Paper Trading ────────────────────────────────────────────────────────────
export interface PaperTrade {
  id: string
  assetId: string
  assetName: string
  assetSymbol: string
  type: 'BUY' | 'SELL'
  amount: number
  price: number
  botAction: 'BUY' | 'SELL' | 'HOLD'
  userResult: 'WIN' | 'LOSS' | 'NEUTRAL' | null
  botResult: 'WIN' | 'LOSS' | 'NEUTRAL' | null
  analysis: TradeAnalysis | null
  timestamp: string
  resolvedAt: string | null
}

export interface TradeAnalysis {
  actualOutcome: string
  userReason: string
  botReason: string
  lesson: string
  priceAtClose: number
  pnlPercent: number
}

export interface PaperPortfolio {
  cash: number
  trades: PaperTrade[]
  holdings: Record<string, { quantity: number; avgPrice: number }>
}

// ─── News ─────────────────────────────────────────────────────────────────────
export interface NewsItem {
  id: string
  title: string
  summary: string
  source: string
  url: string
  publishedAt: string
  sentiment: 'positive' | 'negative' | 'neutral'
  affectedAssets: string[]        // asset IDs
  affectedClasses: AssetClass[]
  impact: 'high' | 'medium' | 'low'
}

// ─── HITL / Human Contribution ───────────────────────────────────────────────
export type QuestionType = 'MCQ' | 'SAQ'

export interface HITLQuestion {
  id: string
  level: number
  type: QuestionType
  question: string
  options?: string[]      // MCQ only
  correctAnswer?: string  // MCQ only
  context: string
  reward: number          // paper cash earned
}

export interface HITLProgress {
  currentLevel: number
  xp: number
  xpForNextLevel: number
  totalContributions: number
  correctAnswers: number
  cashEarned: number
  completedLevels: number[]
  history: ContributionRecord[]
}

export interface ContributionRecord {
  id: string
  questionId: string
  question: string
  userAnswer: string
  correct: boolean
  cashEarned: number
  timestamp: string
}

// ─── User ─────────────────────────────────────────────────────────────────────
export interface User {
  id: string
  name: string
  email: string
  avatar: string
  paperCash: number
  trackedAssets: string[]
  joinedAt: string
}
