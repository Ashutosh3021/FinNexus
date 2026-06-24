import type {
  Asset, Prediction, PredictionRecord, MonthlyPerformance,
  PaperTrade, NewsItem, HITLQuestion, HITLProgress, User
} from '../types'

// ─── Mock User ────────────────────────────────────────────────────────────────
export const mockUser: User = {
  id: 'user-1',
  name: 'Arjun Sharma',
  email: 'arjun@example.com',
  avatar: 'AS',
  paperCash: 100,
  trackedAssets: ['btc', 'eth', 'nifty50', 'gold'],
  joinedAt: '2026-01-15',
}

// ─── Chart Generators ─────────────────────────────────────────────────────────
function generateChart(base: number, days: number, volatility: number) {
  const data = []
  let price = base
  const now = new Date('2026-06-24')
  for (let i = days; i >= 0; i--) {
    const d = new Date(now)
    d.setDate(d.getDate() - i)
    price = price * (1 + (Math.random() - 0.48) * volatility)
    data.push({
      date: d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' }),
      price: Math.round(price * 100) / 100,
    })
  }
  return data
}

// ─── Assets ───────────────────────────────────────────────────────────────────
export const mockAssets: Asset[] = [
  // Crypto
  {
    id: 'btc', symbol: 'BTC', name: 'Bitcoin', assetClass: 'Crypto',
    price: 6842300, priceFormatted: '₹68,42,300', change: 2.4, changeFormatted: '+2.4%',
    volume: '$34.2B', lastUpdated: '2026-06-24 15:30', trend: 'Bullish',
    chartData: generateChart(6200000, 30, 0.03),
  },
  {
    id: 'eth', symbol: 'ETH', name: 'Ethereum', assetClass: 'Crypto',
    price: 284150, priceFormatted: '₹2,84,150', change: -0.5, changeFormatted: '-0.5%',
    volume: '$12.1B', lastUpdated: '2026-06-24 15:30', trend: 'Neutral',
    chartData: generateChart(270000, 30, 0.03),
  },
  {
    id: 'sol', symbol: 'SOL', name: 'Solana', assetClass: 'Crypto',
    price: 12850, priceFormatted: '₹12,850', change: -4.2, changeFormatted: '-4.2%',
    volume: '$3.8B', lastUpdated: '2026-06-24 15:30', trend: 'Bearish',
    chartData: generateChart(14000, 30, 0.04),
  },
  {
    id: 'bnb', symbol: 'BNB', name: 'BNB', assetClass: 'Crypto',
    price: 49200, priceFormatted: '₹49,200', change: 1.1, changeFormatted: '+1.1%',
    volume: '$2.1B', lastUpdated: '2026-06-24 15:30', trend: 'Bullish',
    chartData: generateChart(47000, 30, 0.025),
  },
  // Stocks
  {
    id: 'reliance', symbol: 'RELIANCE', name: 'Reliance Industries', assetClass: 'Stocks',
    price: 2960, priceFormatted: '₹2,960', change: 1.8, changeFormatted: '+1.8%',
    volume: '₹2,400Cr', lastUpdated: '2026-06-24 15:30', trend: 'Bullish',
    chartData: generateChart(2800, 30, 0.015),
  },
  {
    id: 'tcs', symbol: 'TCS', name: 'Tata Consultancy Services', assetClass: 'Stocks',
    price: 3880, priceFormatted: '₹3,880', change: -0.3, changeFormatted: '-0.3%',
    volume: '₹1,800Cr', lastUpdated: '2026-06-24 15:30', trend: 'Neutral',
    chartData: generateChart(3900, 30, 0.012),
  },
  {
    id: 'hdfc', symbol: 'HDFCBANK', name: 'HDFC Bank', assetClass: 'Stocks',
    price: 1720, priceFormatted: '₹1,720', change: 0.6, changeFormatted: '+0.6%',
    volume: '₹3,100Cr', lastUpdated: '2026-06-24 15:30', trend: 'Bullish',
    chartData: generateChart(1680, 30, 0.012),
  },
  {
    id: 'infosys', symbol: 'INFY', name: 'Infosys', assetClass: 'Stocks',
    price: 1540, priceFormatted: '₹1,540', change: -1.2, changeFormatted: '-1.2%',
    volume: '₹1,400Cr', lastUpdated: '2026-06-24 15:30', trend: 'Bearish',
    chartData: generateChart(1580, 30, 0.015),
  },
  // ETFs
  {
    id: 'spy', symbol: 'SPY', name: 'SPDR S&P 500 ETF', assetClass: 'ETFs',
    price: 45600, priceFormatted: '$546.00', change: 0.8, changeFormatted: '+0.8%',
    volume: '$28.4B', lastUpdated: '2026-06-24 15:30', trend: 'Bullish',
    chartData: generateChart(44000, 30, 0.008),
  },
  {
    id: 'qqq', symbol: 'QQQ', name: 'Invesco QQQ Trust', assetClass: 'ETFs',
    price: 39800, priceFormatted: '$477.60', change: 1.2, changeFormatted: '+1.2%',
    volume: '$12.9B', lastUpdated: '2026-06-24 15:30', trend: 'Bullish',
    chartData: generateChart(38000, 30, 0.01),
  },
  {
    id: 'gld', symbol: 'GLD', name: 'SPDR Gold Shares', assetClass: 'ETFs',
    price: 18950, priceFormatted: '$227.40', change: 0.4, changeFormatted: '+0.4%',
    volume: '$1.8B', lastUpdated: '2026-06-24 15:30', trend: 'Neutral',
    chartData: generateChart(18500, 30, 0.008),
  },
  // Futures
  {
    id: 'nifty50', symbol: 'NIFTY50', name: 'Nifty 50 Futures', assetClass: 'Futures',
    price: 24580, priceFormatted: '₹24,580', change: 0.9, changeFormatted: '+0.9%',
    volume: '₹48,200Cr', lastUpdated: '2026-06-24 15:30', trend: 'Bullish',
    chartData: generateChart(24000, 30, 0.01),
  },
  {
    id: 'banknifty', symbol: 'BANKNIFTY', name: 'Bank Nifty Futures', assetClass: 'Futures',
    price: 52140, priceFormatted: '₹52,140', change: -0.7, changeFormatted: '-0.7%',
    volume: '₹32,400Cr', lastUpdated: '2026-06-24 15:30', trend: 'Neutral',
    chartData: generateChart(53000, 30, 0.012),
  },
  // Commodities
  {
    id: 'gold', symbol: 'GOLD', name: 'Gold', assetClass: 'Commodities',
    price: 72400, priceFormatted: '₹72,400/10g', change: 0.5, changeFormatted: '+0.5%',
    volume: '$54.2B', lastUpdated: '2026-06-24 15:30', trend: 'Bullish',
    chartData: generateChart(70000, 30, 0.008),
  },
  {
    id: 'crude', symbol: 'CRUDE', name: 'Brent Crude Oil', assetClass: 'Commodities',
    price: 6820, priceFormatted: '$81.80/bbl', change: -1.1, changeFormatted: '-1.1%',
    volume: '$18.4B', lastUpdated: '2026-06-24 15:30', trend: 'Bearish',
    chartData: generateChart(7200, 30, 0.02),
  },
  {
    id: 'silver', symbol: 'SILVER', name: 'Silver', assetClass: 'Commodities',
    price: 88500, priceFormatted: '₹88,500/kg', change: 1.6, changeFormatted: '+1.6%',
    volume: '$6.1B', lastUpdated: '2026-06-24 15:30', trend: 'Bullish',
    chartData: generateChart(85000, 30, 0.018),
  },
]

// ─── Predictions ──────────────────────────────────────────────────────────────
export const mockPredictions: Prediction[] = [
  {
    assetId: 'btc', signal: 'BUY', confidence: 74, modelPerformance: 78,
    reasoning: 'Strong on-chain accumulation, whale wallets +18% over 7D. RSI recovering from oversold. Positive macro sentiment.',
    mlSignal: 'BUY', ragSignal: 'BUY', botSignal: 'HOLD',
    timestamp: '2026-06-24 15:00',
  },
  {
    assetId: 'eth', signal: 'HOLD', confidence: 61, modelPerformance: 72,
    reasoning: 'Consolidation phase near key resistance. Layer-2 activity strong but ETH price lagging. Wait for confirmation.',
    mlSignal: 'HOLD', ragSignal: 'BUY', botSignal: 'HOLD',
    timestamp: '2026-06-24 15:00',
  },
  {
    assetId: 'sol', signal: 'SELL', confidence: 68, modelPerformance: 65,
    reasoning: 'Bearish divergence on 4H chart. Network congestion increasing. Institutional outflows detected.',
    mlSignal: 'SELL', ragSignal: 'SELL', botSignal: 'HOLD',
    timestamp: '2026-06-24 15:00',
  },
  {
    assetId: 'reliance', signal: 'BUY', confidence: 82, modelPerformance: 84,
    reasoning: 'Q1 results beat expectations by 12%. Jio platform MAU +8% QoQ. Retail expansion on track.',
    mlSignal: 'BUY', ragSignal: 'BUY', botSignal: 'BUY',
    timestamp: '2026-06-24 15:00',
  },
  {
    assetId: 'nifty50', signal: 'BUY', confidence: 71, modelPerformance: 76,
    reasoning: 'FII net buyers 5th consecutive session. RBI rate hold positive for markets. Election year rally pattern.',
    mlSignal: 'BUY', ragSignal: 'BUY', botSignal: 'HOLD',
    timestamp: '2026-06-24 15:00',
  },
  {
    assetId: 'gold', signal: 'HOLD', confidence: 55, modelPerformance: 69,
    reasoning: 'USD strengthening limits upside. Geopolitical risk premium still elevated. Wait for Fed signals.',
    mlSignal: 'HOLD', ragSignal: 'HOLD', botSignal: 'BUY',
    timestamp: '2026-06-24 15:00',
  },
]

// ─── Prediction Records ───────────────────────────────────────────────────────
export const mockPredictionHistory: PredictionRecord[] = [
  { id: 'p1', assetId: 'btc', assetName: 'Bitcoin', signal: 'BUY', confidence: 72, actual: 'BUY', correct: true, date: '2026-06-23' },
  { id: 'p2', assetId: 'eth', assetName: 'Ethereum', signal: 'HOLD', confidence: 58, actual: 'SELL', correct: false, date: '2026-06-23' },
  { id: 'p3', assetId: 'sol', assetName: 'Solana', signal: 'SELL', confidence: 65, actual: 'SELL', correct: true, date: '2026-06-22' },
  { id: 'p4', assetId: 'reliance', assetName: 'Reliance', signal: 'BUY', confidence: 80, actual: 'BUY', correct: true, date: '2026-06-22' },
  { id: 'p5', assetId: 'nifty50', assetName: 'Nifty 50', signal: 'BUY', confidence: 68, actual: 'BUY', correct: true, date: '2026-06-21' },
  { id: 'p6', assetId: 'gold', assetName: 'Gold', signal: 'HOLD', confidence: 52, actual: 'BUY', correct: false, date: '2026-06-21' },
  { id: 'p7', assetId: 'btc', assetName: 'Bitcoin', signal: 'BUY', confidence: 70, actual: 'BUY', correct: true, date: '2026-06-20' },
  { id: 'p8', assetId: 'crude', assetName: 'Brent Crude', signal: 'SELL', confidence: 60, actual: 'SELL', correct: true, date: '2026-06-20' },
  { id: 'p9', assetId: 'bnb', assetName: 'BNB', signal: 'HOLD', confidence: 55, actual: 'BUY', correct: false, date: '2026-06-19' },
  { id: 'p10', assetId: 'tcs', assetName: 'TCS', signal: 'HOLD', confidence: 63, actual: 'HOLD', correct: true, date: '2026-06-19' },
  { id: 'p11', assetId: 'hdfc', assetName: 'HDFC Bank', signal: 'BUY', confidence: 75, actual: 'BUY', correct: true, date: '2026-06-18' },
  { id: 'p12', assetId: 'spy', assetName: 'SPY', signal: 'BUY', confidence: 71, actual: 'BUY', correct: true, date: '2026-06-18' },
  { id: 'p13', assetId: 'eth', assetName: 'Ethereum', signal: 'SELL', confidence: 62, actual: 'HOLD', correct: false, date: '2026-06-17' },
  { id: 'p14', assetId: 'silver', assetName: 'Silver', signal: 'BUY', confidence: 66, actual: 'BUY', correct: true, date: '2026-06-17' },
  { id: 'p15', assetId: 'infosys', assetName: 'Infosys', signal: 'SELL', confidence: 58, actual: 'SELL', correct: true, date: '2026-06-16' },
  { id: 'p16', assetId: 'btc', assetName: 'Bitcoin', signal: 'BUY', confidence: 77, actual: 'BUY', correct: true, date: '2026-06-16' },
  { id: 'p17', assetId: 'banknifty', assetName: 'Bank Nifty', signal: 'HOLD', confidence: 60, actual: 'SELL', correct: false, date: '2026-06-15' },
  { id: 'p18', assetId: 'gold', assetName: 'Gold', signal: 'BUY', confidence: 69, actual: 'BUY', correct: true, date: '2026-06-15' },
  { id: 'p19', assetId: 'sol', assetName: 'Solana', signal: 'SELL', confidence: 72, actual: 'SELL', correct: true, date: '2026-06-14' },
  { id: 'p20', assetId: 'qqq', assetName: 'QQQ', signal: 'BUY', confidence: 74, actual: 'BUY', correct: true, date: '2026-06-14' },
  { id: 'p21', assetId: 'btc', assetName: 'Bitcoin', signal: 'HOLD', confidence: 55, actual: null, correct: null, date: '2026-06-24' },
  { id: 'p22', assetId: 'reliance', assetName: 'Reliance', signal: 'BUY', confidence: 82, actual: null, correct: null, date: '2026-06-24' },
  { id: 'p23', assetId: 'nifty50', assetName: 'Nifty 50', signal: 'BUY', confidence: 71, actual: null, correct: null, date: '2026-06-24' },
]

export const mockMonthlyPerformance: MonthlyPerformance[] = [
  { month: 'Jan', accuracy: 62, predictions: 18 },
  { month: 'Feb', accuracy: 65, predictions: 20 },
  { month: 'Mar', accuracy: 70, predictions: 22 },
  { month: 'Apr', accuracy: 68, predictions: 24 },
  { month: 'May', accuracy: 73, predictions: 26 },
  { month: 'Jun', accuracy: 76, predictions: 23 },
]

// ─── Paper Trades ─────────────────────────────────────────────────────────────
export const mockPaperTrades: PaperTrade[] = [
  {
    id: 'trade-1', assetId: 'btc', assetName: 'Bitcoin', assetSymbol: 'BTC',
    type: 'BUY', amount: 20, price: 6720000, botAction: 'SELL',
    userResult: 'WIN', botResult: 'LOSS',
    analysis: {
      actualOutcome: 'BTC rose 1.8% over the next 24 hours.',
      userReason: 'User correctly identified the bullish divergence on MACD.',
      botReason: 'Bot over-weighted short-term sell signal from news sentiment.',
      lesson: 'Technical confluence can override short-term news noise.',
      priceAtClose: 6841000, pnlPercent: 1.8,
    },
    timestamp: '2026-06-23 10:00', resolvedAt: '2026-06-24 10:00',
  },
]

// ─── News ─────────────────────────────────────────────────────────────────────
export const mockNews: NewsItem[] = [
  {
    id: 'n1',
    title: 'Federal Reserve Holds Rates, Signals Two Cuts in 2026',
    summary: 'Fed Chair Jerome Powell confirmed rates will stay at 5.25-5.50% but indicated two 25bps cuts remain on the table for H2 2026, lifting risk assets globally.',
    source: 'Reuters', url: '#', publishedAt: '2026-06-24 14:30',
    sentiment: 'positive',
    affectedAssets: ['btc', 'eth', 'spy', 'qqq', 'nifty50'],
    affectedClasses: ['Crypto', 'ETFs', 'Stocks'],
    impact: 'high',
  },
  {
    id: 'n2',
    title: 'Bitcoin Spot ETF Sees Record $1.2B Inflow in Single Day',
    summary: 'BlackRock\'s IBIT ETF recorded its largest single-day inflow since launch, signalling continued institutional accumulation ahead of the halving anniversary.',
    source: 'CoinDesk', url: '#', publishedAt: '2026-06-24 13:15',
    sentiment: 'positive',
    affectedAssets: ['btc', 'eth', 'bnb'],
    affectedClasses: ['Crypto', 'ETFs'],
    impact: 'high',
  },
  {
    id: 'n3',
    title: 'Reliance Q1 Results Beat Street Estimates by 12%',
    summary: 'RIL reported consolidated net profit of ₹19,800 crore, driven by strong performance in Jio Platforms and Retail segments.',
    source: 'Economic Times', url: '#', publishedAt: '2026-06-24 12:00',
    sentiment: 'positive',
    affectedAssets: ['reliance', 'nifty50', 'banknifty'],
    affectedClasses: ['Stocks', 'Futures'],
    impact: 'medium',
  },
  {
    id: 'n4',
    title: 'OPEC+ Agrees to Extend Production Cuts Through Q4 2026',
    summary: 'The oil cartel extended voluntary output cuts of 3.66M bpd through December 2026, providing support to crude oil prices amid demand uncertainty.',
    source: 'Bloomberg', url: '#', publishedAt: '2026-06-24 11:45',
    sentiment: 'positive',
    affectedAssets: ['crude', 'gld'],
    affectedClasses: ['Commodities', 'ETFs'],
    impact: 'medium',
  },
  {
    id: 'n5',
    title: 'SEC Approves Additional Crypto ETF Products',
    summary: 'The SEC greenlit three new spot altcoin ETFs, including products tracking Ethereum and Solana, expanding institutional crypto access.',
    source: 'Financial Times', url: '#', publishedAt: '2026-06-24 10:20',
    sentiment: 'positive',
    affectedAssets: ['eth', 'sol', 'btc'],
    affectedClasses: ['Crypto', 'ETFs'],
    impact: 'high',
  },
  {
    id: 'n6',
    title: 'Infosys Issues Soft Revenue Guidance for FY27',
    summary: 'Infosys guided for revenue growth of 4-6% in constant currency for FY27, slightly below analyst expectations of 6-8%, citing client budget caution in BFSI.',
    source: 'Mint', url: '#', publishedAt: '2026-06-24 09:30',
    sentiment: 'negative',
    affectedAssets: ['infosys', 'tcs', 'nifty50'],
    affectedClasses: ['Stocks', 'Futures'],
    impact: 'medium',
  },
  {
    id: 'n7',
    title: 'Gold Tests $2,400 Resistance as Dollar Weakens',
    summary: 'Gold futures are testing the key $2,400/oz resistance level following dollar weakness post-Fed statement. Analysts see breakout potential if confirmed.',
    source: 'Kitco', url: '#', publishedAt: '2026-06-24 08:50',
    sentiment: 'positive',
    affectedAssets: ['gold', 'silver', 'gld'],
    affectedClasses: ['Commodities', 'ETFs'],
    impact: 'medium',
  },
  {
    id: 'n8',
    title: 'Bank Nifty Options OI Data Shows Bearish Bias',
    summary: 'Derivatives data shows heavy put writing at 52,000 and call writing at 53,500, suggesting traders expect consolidation with a slight downward bias.',
    source: 'NSE Analytics', url: '#', publishedAt: '2026-06-24 09:00',
    sentiment: 'negative',
    affectedAssets: ['banknifty', 'hdfc'],
    affectedClasses: ['Futures', 'Stocks'],
    impact: 'low',
  },
]

// ─── HITL Questions ───────────────────────────────────────────────────────────
export const hitlQuestions: HITLQuestion[] = [
  // Level 1
  {
    id: 'q1', level: 1, type: 'MCQ',
    question: 'When a stock\'s RSI crosses above 70, it is typically considered:',
    options: ['Oversold — good time to buy', 'Overbought — potential reversal zone', 'Neutral — no action needed', 'A strong buy signal'],
    correctAnswer: 'Overbought — potential reversal zone',
    context: 'RSI (Relative Strength Index) measures momentum. Values above 70 typically indicate overbought conditions.',
    reward: 5,
  },
  {
    id: 'q2', level: 1, type: 'MCQ',
    question: 'Bitcoin just broke above its 200-day moving average with high volume. This is most likely:',
    options: ['A bearish signal', 'A bullish breakout confirmation', 'An irrelevant technical event', 'A sell signal'],
    correctAnswer: 'A bullish breakout confirmation',
    context: 'Moving average crossovers with volume confirmation are widely used trend signals.',
    reward: 5,
  },
  {
    id: 'q3', level: 1, type: 'SAQ',
    question: 'Reliance Industries just announced a major international acquisition. How would you expect the stock to react in the short term, and why?',
    context: 'Acquisitions are major corporate events. Consider both market sentiment and financial impact.',
    reward: 10,
  },
  // Level 2
  {
    id: 'q4', level: 2, type: 'MCQ',
    question: 'A candlestick pattern showing a small body with long wicks on both sides is called:',
    options: ['Doji — signals indecision', 'Hammer — strong buy signal', 'Shooting Star — bearish reversal', 'Marubozu — strong trend'],
    correctAnswer: 'Doji — signals indecision',
    context: 'Candlestick patterns provide visual cues about buying/selling pressure.',
    reward: 8,
  },
  {
    id: 'q5', level: 2, type: 'MCQ',
    question: 'If gold prices rise sharply on a day when the USD Index (DXY) also rises strongly, what does this suggest?',
    options: ['Normal market behavior', 'An unusual breakdown of the typical inverse correlation — potential panic buying', 'Gold is tracking equities', 'Nothing significant'],
    correctAnswer: 'An unusual breakdown of the typical inverse correlation — potential panic buying',
    context: 'Gold and USD typically have an inverse relationship. When both rise together, it often signals a flight to safety.',
    reward: 8,
  },
  // Level 3
  {
    id: 'q6', level: 3, type: 'MCQ',
    question: 'In options trading, a "theta" of -0.05 for an option means:',
    options: ['The option gains ₹0.05 per day', 'The option loses ₹0.05 in value per day due to time decay', 'The option has 5% chance of expiring in the money', 'Delta is 5%'],
    correctAnswer: 'The option loses ₹0.05 in value per day due to time decay',
    context: 'Options Greeks measure various risk dimensions. Theta represents time decay.',
    reward: 12,
  },
  {
    id: 'q7', level: 3, type: 'SAQ',
    question: 'Nifty 50 futures are trading at a 150-point premium to spot. Is this normal? What does it indicate about market expectations?',
    context: 'Futures basis (premium/discount) reflects carry cost and market sentiment.',
    reward: 15,
  },
]

export const mockHITLProgress: HITLProgress = {
  currentLevel: 2,
  xp: 340,
  xpForNextLevel: 500,
  totalContributions: 8,
  correctAnswers: 6,
  cashEarned: 52,
  completedLevels: [1],
  history: [
    { id: 'h1', questionId: 'q1', question: 'When RSI crosses above 70...', userAnswer: 'Overbought — potential reversal zone', correct: true, cashEarned: 5, timestamp: '2026-06-20 10:00' },
    { id: 'h2', questionId: 'q2', question: 'Bitcoin breaks 200-day MA...', userAnswer: 'A bullish breakout confirmation', correct: true, cashEarned: 5, timestamp: '2026-06-21 11:00' },
    { id: 'h3', questionId: 'q3', question: 'Reliance acquisition...', userAnswer: 'Positive reaction initially due to growth optimism, but may face volatility if deal terms are unfavorable.', correct: true, cashEarned: 10, timestamp: '2026-06-22 14:00' },
  ],
}
