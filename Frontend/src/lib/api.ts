/**
 * FinNexus API Client
 * All backend communication goes through this module.
 */

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

// ── Token storage ─────────────────────────────────────────────────────────────

let _token: string | null = null

export function setToken(token: string): void {
  _token = token
  localStorage.setItem('finnexus_token', token)
}

export function getToken(): string | null {
  if (_token) return _token
  _token = localStorage.getItem('finnexus_token')
  return _token
}

export function clearToken(): void {
  _token = null
  localStorage.removeItem('finnexus_token')
}

// ── Core fetch wrapper ────────────────────────────────────────────────────────

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  requireAuth = true,
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> ?? {}),
  }

  if (requireAuth) {
    const token = getToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  })

  if (res.status === 401) {
    clearToken()
    throw new Error('Unauthorized — please log in again')
  }

  if (!res.ok) {
    let detail = `HTTP ${res.status}`
    try {
      const body = await res.json()
      detail = body.detail ?? detail
    } catch { /* ignore */ }
    throw new Error(detail)
  }

  return res.json() as Promise<T>
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export interface LoginResponse {
  access_token: string
  token_type: string
  user_id: number
  expires_in: number
}

export async function login(userId: string | number): Promise<LoginResponse> {
  // Backend expects an integer user_id — coerce string IDs (e.g. 'user-1') to a numeric hash
  const numericId = typeof userId === 'number'
    ? userId
    : parseInt(userId.replace(/\D/g, ''), 10) || 1
  const resp = await apiFetch<LoginResponse>('/auth/token', {
    method: 'POST',
    body: JSON.stringify({ user_id: numericId }),
  }, false)
  setToken(resp.access_token)
  return resp
}

// ── Health ────────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string
  service: string
}

export async function healthCheck(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>('/health', {}, false)
}

// ── Session ───────────────────────────────────────────────────────────────────

export interface MarketContextPayload {
  regime?: string
  vix_level?: number
  dxy_trend?: string
  news?: string[]
  prices?: Record<string, number>
  trends?: Record<string, string>
  user_portfolio?: string
  user_history_summary?: string
}

export interface StartSessionRequest {
  user_id: number
  level?: number
  asset_context?: string
  force_new?: boolean
  market_context?: MarketContextPayload
}

export interface Question {
  id: string
  level: number
  type: 'mcq_single' | 'mcq_multiple' | 'saq'
  question: string
  asset_class: string
  asset_symbol: string
  context: string
  options: string[]
  correct_answer: string | null
  word_limit: number
  difficulty: number
  tags: string[]
}

export interface SessionResponse {
  session_id: string
  level: number
  total_questions: number
  progress: string
  first_question?: Question
  message: string
}

export async function startSession(req: StartSessionRequest): Promise<SessionResponse> {
  return apiFetch<SessionResponse>('/session/start', {
    method: 'POST',
    body: JSON.stringify({
      user_id: req.user_id,
      level: req.level ?? 1,
      asset_context: req.asset_context ?? '',
      force_new: req.force_new ?? false,
      regime: req.market_context?.regime ?? 'neutral',
      vix_level: req.market_context?.vix_level ?? 18.0,
      dxy_trend: req.market_context?.dxy_trend ?? 'flat',
      news: req.market_context?.news ?? [],
      prices: req.market_context?.prices ?? {},
      trends: req.market_context?.trends ?? {},
      user_portfolio: req.market_context?.user_portfolio ?? '',
      user_history_summary: req.market_context?.user_history_summary ?? '',
    }),
  })
}

export async function getCurrentQuestion(userId: number): Promise<Question> {
  return apiFetch<Question>(`/session/question?user_id=${userId}`)
}

export interface AnswerResponse {
  status: 'in_progress' | 'level_complete'
  score: number
  progress: string
  feedback?: string
  next_question?: Question
  level_result?: LevelResult
}

// ── V2 Session (async bulk) ────────────────────────────────────────────────────

export interface StartSessionV2Response {
  session_id: string
  level: number
  total_questions: number
  questions: Question[]
}

export async function startSessionV2(userId: number, level: number, forceNew = false): Promise<StartSessionV2Response> {
  return apiFetch<StartSessionV2Response>('/v2/session/start', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, level, force_new: forceNew }),
  })
}

export async function submitAnswersV2(
  sessionId: string,
  answers: Record<string, string | number>,
): Promise<Record<string, unknown>> {
  return apiFetch('/v2/session/answers', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, answers }),
  })
}

// ── User ──────────────────────────────────────────────────────────────────────

export interface UserStats {
  user_id: number
  total_sessions: number
  completed_levels: number[]
  total_cash_earned: number
  average_score: number
  proficiency: number
  current_level: number
  total_correct: number
  total_answered: number
  accuracy: number
  best_level_score: number
  recent_activity: Record<string, unknown>[]
}

export interface LevelResult {
  level: number
  score: number
  reward: number
  next_level: number
  level_up: boolean
  is_level_20: boolean
  level_20_bonus: number
  message: string
}

// ── User ID coercion helper ───────────────────────────────────────────────────
function toNumericId(userId: string | number): number {
  return typeof userId === 'number'
    ? userId
    : parseInt(userId.replace(/\D/g, ''), 10) || 1
}

export async function getUserStats(userId: string | number): Promise<UserStats> {
  return apiFetch<UserStats>(`/user/${toNumericId(userId)}/stats`)
}

export async function getPaperCash(userId: string | number): Promise<{ user_id: number; paper_cash: number }> {
  return apiFetch(`/user/${toNumericId(userId)}/cash`)
}

export async function predictImprovement(userId: string | number): Promise<{ user_id: number; predicted_improvement: number }> {
  return apiFetch(`/user/${toNumericId(userId)}/predict`)
}

export async function submitAnswer(userId: string | number, answer: string | number | string[]): Promise<AnswerResponse> {
  return apiFetch<AnswerResponse>('/session/answer', {
    method: 'POST',
    body: JSON.stringify({ user_id: toNumericId(userId), answer }),
  })
}

export async function assessStartingLevel(
  userId: number,
  proficiencyScore: number,
): Promise<{ user_id: number; proficiency_score: number; recommended_level: number }> {
  return apiFetch('/assess', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, proficiency_score: proficiencyScore }),
  })
}

// ── RAG ───────────────────────────────────────────────────────────────────────

export async function ragStats(): Promise<Record<string, unknown>> {
  return apiFetch('/rag/stats')
}

export async function ragRetrieve(
  query: string,
  collection: 'market_data' | 'news_events' | 'trading_theories' = 'trading_theories',
): Promise<Record<string, unknown>> {
  return apiFetch(`/rag/retrieve?query=${encodeURIComponent(query)}&collection=${collection}`)
}

// ── Market data (external / scraper endpoints) ────────────────────────────────
// NOTE: The FastAPI backend does not currently expose /market/* routes.
// These calls proxy through Vite → backend, and fall back gracefully if missing.

export interface MarketPrice {
  id: string
  symbol: string
  name: string
  price: number
  change_percent: number
  volume: string
  last_updated: string
  trend: 'Bullish' | 'Bearish' | 'Neutral'
  asset_class: 'Stocks' | 'Crypto' | 'ETFs' | 'Futures' | 'Commodities'
}

export interface MarketTrend {
  id: string
  symbol: string
  name: string
  trend_1d: 'Bullish' | 'Bearish' | 'Neutral'
  trend_1w: 'Bullish' | 'Bearish' | 'Neutral'
  trend_1m: 'Bullish' | 'Bearish' | 'Neutral'
  asset_class: string
}

export interface MarketNewsItem {
  id: string
  title: string
  summary: string
  source: string
  url: string
  published_at: string
  sentiment: 'positive' | 'negative' | 'neutral'
  affected_assets: string[]
  affected_classes: string[]
  impact: 'high' | 'medium' | 'low'
}

export async function getMarketPrices(): Promise<{ prices: MarketPrice[] }> {
  return apiFetch('/market/prices', {}, false)
}

export async function getMarketTrends(
  timeframe = '1D',
  assetClass?: string,
): Promise<{ trends: MarketTrend[] }> {
  const params = new URLSearchParams({ timeframe })
  if (assetClass && assetClass !== 'All') params.set('asset_class', assetClass)
  return apiFetch(`/market/trends?${params}`, {}, false)
}

export async function getMarketNews(
  limit = 20,
  filter?: string,
): Promise<{ news: MarketNewsItem[] }> {
  const params = new URLSearchParams({ limit: String(limit) })
  if (filter && filter !== 'All') params.set('filter', filter)
  return apiFetch(`/market/news?${params}`, {}, false)
}

// ── User profile (onboarding) ─────────────────────────────────────────────────

export interface UpdateProfileRequest {
  user_id: number
  name?: string
  email?: string
  current_level?: number
  tracked_assets?: string[]
  experience?: string
}

export async function updateUserProfile(
  req: UpdateProfileRequest,
): Promise<Record<string, unknown>> {
  return apiFetch('/user/profile', {
    method: 'POST',
    body: JSON.stringify(req),
  })
}

// ── Generic API error ─────────────────────────────────────────────────────────

export class ApiError extends Error {
  readonly status?: number;
  
  constructor(
    message: string,
    status?: number,
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status;
  }
}
