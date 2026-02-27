// Mock User Data
export const mockUser = {
  id: 'user_001',
  name: 'Alex Johnson',
  email: 'alex@finnexus.com',
  level: 'INTERMEDIATE',
  virtualBalance: 124500.50,
  xp: 7250,
  avatar: '/placeholder-user.jpg',
  joinDate: '2024-01-15',
};

// Mock Portfolio Holdings
export const mockPortfolio = [
  {
    id: 'holding_001',
    asset: 'Apple Inc.',
    symbol: 'AAPL',
    type: 'stock',
    qty: 25,
    buyPrice: 150.25,
    currentPrice: 185.40,
    buyDate: '2024-03-01',
  },
  {
    id: 'holding_002',
    asset: 'Bitcoin',
    symbol: 'BTC',
    type: 'crypto',
    qty: 0.5,
    buyPrice: 42500,
    currentPrice: 52300,
    buyDate: '2024-02-15',
  },
  {
    id: 'holding_003',
    asset: 'Gold (oz)',
    symbol: 'GOLD',
    type: 'commodity',
    qty: 10,
    buyPrice: 2050,
    currentPrice: 2140,
    buyDate: '2024-01-20',
  },
  {
    id: 'holding_004',
    asset: 'S&P 500 ETF',
    symbol: 'SPY',
    type: 'etf',
    qty: 40,
    buyPrice: 450.75,
    currentPrice: 485.20,
    buyDate: '2024-02-10',
  },
  {
    id: 'holding_005',
    asset: 'Microsoft Corp',
    symbol: 'MSFT',
    type: 'stock',
    qty: 15,
    buyPrice: 380.50,
    currentPrice: 425.10,
    buyDate: '2024-03-15',
  },
  {
    id: 'holding_006',
    asset: 'Ethereum',
    symbol: 'ETH',
    type: 'crypto',
    qty: 2.5,
    buyPrice: 2300,
    currentPrice: 3200,
    buyDate: '2024-02-28',
  },
];

// Mock Prediction History
export const mockPredictionHistory = [
  {
    id: 'pred_001',
    asset: 'AAPL',
    type: 'win',
    prediction: 'up',
    actual: 'up',
    pnl: 2450,
    pnlPercent: 5.2,
    date: '2024-03-20',
  },
  {
    id: 'pred_002',
    asset: 'BTC',
    type: 'win',
    prediction: 'down',
    actual: 'down',
    pnl: 1875,
    pnlPercent: 8.5,
    date: '2024-03-19',
  },
  {
    id: 'pred_003',
    asset: 'SPY',
    type: 'loss',
    prediction: 'up',
    actual: 'down',
    pnl: -950,
    pnlPercent: -3.2,
    date: '2024-03-18',
  },
  {
    id: 'pred_004',
    asset: 'MSFT',
    type: 'win',
    prediction: 'up',
    actual: 'up',
    pnl: 1640,
    pnlPercent: 4.8,
    date: '2024-03-17',
  },
  {
    id: 'pred_005',
    asset: 'ETH',
    type: 'win',
    prediction: 'up',
    actual: 'up',
    pnl: 2300,
    pnlPercent: 9.2,
    date: '2024-03-16',
  },
  {
    id: 'pred_006',
    asset: 'GOLD',
    type: 'loss',
    prediction: 'down',
    actual: 'up',
    pnl: -520,
    pnlPercent: -2.1,
    date: '2024-03-15',
  },
  {
    id: 'pred_007',
    asset: 'AAPL',
    type: 'win',
    prediction: 'up',
    actual: 'up',
    pnl: 1820,
    pnlPercent: 6.5,
    date: '2024-03-14',
  },
  {
    id: 'pred_008',
    asset: 'BTC',
    type: 'loss',
    prediction: 'down',
    actual: 'up',
    pnl: -1100,
    pnlPercent: -5.2,
    date: '2024-03-13',
  },
];

// Mock News Feed
export const mockNews = [
  {
    id: 'news_001',
    headline: 'Fed Signals Stable Interest Rates Through 2024',
    category: 'macro',
    sentiment: 'neutral',
    impactScore: 7,
    affectedAssets: ['SPY', 'MSFT', 'AAPL'],
    summary: 'Federal Reserve officials indicate no immediate changes to monetary policy.',
    geminiAnalysis: 'This signals economic stability but may limit growth expectations for the broader market.',
    date: '2024-03-21',
    source: 'Reuters',
  },
  {
    id: 'news_002',
    headline: 'Bitcoin Hits New All-Time High',
    category: 'crypto',
    sentiment: 'positive',
    impactScore: 9,
    affectedAssets: ['BTC', 'ETH'],
    summary: 'Bitcoin surges past previous record amid institutional adoption.',
    geminiAnalysis: 'Strong institutional buying pressure combined with declining inflation signals sustained demand for crypto assets.',
    date: '2024-03-20',
    source: 'CoinDesk',
  },
  {
    id: 'news_003',
    headline: 'Apple Reports Record Q1 iPhone Sales',
    category: 'earnings',
    sentiment: 'positive',
    impactScore: 8,
    affectedAssets: ['AAPL'],
    summary: 'Apple exceeds expectations with strong iPhone 15 demand in Asian markets.',
    geminiAnalysis: 'Consumer demand remains robust, supporting continued valuation premium for Apple stock.',
    date: '2024-03-19',
    source: 'Financial Times',
  },
  {
    id: 'news_004',
    headline: 'Oil Prices Decline Amid Demand Concerns',
    category: 'commodities',
    sentiment: 'negative',
    impactScore: 6,
    affectedAssets: ['XLE', 'CVX'],
    summary: 'Global oil prices drop 3% as economic slowdown concerns emerge.',
    geminiAnalysis: 'Energy sector pressure may persist if recession indicators continue deteriorating.',
    date: '2024-03-18',
    source: 'Bloomberg',
  },
  {
    id: 'news_005',
    headline: 'Gold Continues Safe-Haven Rally',
    category: 'commodities',
    sentiment: 'positive',
    impactScore: 5,
    affectedAssets: ['GOLD', 'GLD'],
    summary: 'Gold rises as geopolitical tensions drive investor risk-off positioning.',
    geminiAnalysis: 'Precious metals remain attractive as inflation hedges in uncertain economic environment.',
    date: '2024-03-17',
    source: 'MarketWatch',
  },
  {
    id: 'news_006',
    headline: 'Tech Earnings Season Sets Positive Tone',
    category: 'earnings',
    sentiment: 'positive',
    impactScore: 8,
    affectedAssets: ['MSFT', 'NVDA', 'GOOGL'],
    summary: 'Major tech companies beat profit expectations, raising market optimism.',
    geminiAnalysis: 'Strong earnings and positive guidance suggest continued momentum in technology sector through mid-year.',
    date: '2024-03-16',
    source: 'CNBC',
  },
];

// Mock Learning Progress
export const mockLearningProgress = {
  completedTopics: [
    'stocks-101',
    'technical-analysis-basics',
    'portfolio-diversification',
  ],
  currentTopic: 'risk-management',
  progressPercent: 65,
  weakTopics: ['options-trading', 'derivatives'],
  totalLessonsCompleted: 12,
  lastAccessedDate: '2024-03-21',
};

// Mock Lessons
export const mockLessons = [
  {
    id: 'lesson_001',
    title: 'Introduction to Stock Markets',
    level: 'BEGINNER',
    duration: '15 min',
    content: `
      Learn the fundamentals of stock markets:
      - What are stocks and how do they work
      - Market participants (investors, traders, brokers)
      - How to read stock quotes
      - Understanding market indices (S&P 500, Nasdaq)
    `,
    quiz: [
      {
        id: 'q1',
        question: 'What does a stock represent?',
        options: ['A loan to a company', 'Ownership in a company', 'A commodity', 'A debt instrument'],
        correct: 1,
      },
    ],
  },
  {
    id: 'lesson_002',
    title: 'Technical Analysis Basics',
    level: 'INTERMEDIATE',
    duration: '25 min',
    content: `
      Master the basics of technical analysis:
      - Reading candlestick charts
      - Support and resistance levels
      - Moving averages
      - Key technical indicators
    `,
    quiz: [
      {
        id: 'q2',
        question: 'What does a support level indicate?',
        options: ['Price where selling pressure increases', 'Price where buying pressure typically emerges', 'Maximum price reached', 'Minimum price reached'],
        correct: 1,
      },
    ],
  },
  {
    id: 'lesson_003',
    title: 'Portfolio Diversification',
    level: 'INTERMEDIATE',
    duration: '20 min',
    content: `
      Learn why diversification matters:
      - Risk reduction through asset allocation
      - Correlation between assets
      - Creating a balanced portfolio
      - Rebalancing strategies
    `,
    quiz: [
      {
        id: 'q3',
        question: 'What is the primary benefit of diversification?',
        options: ['Guaranteed profits', 'Risk reduction', 'Higher returns', 'Lower fees'],
        correct: 1,
      },
    ],
  },
  {
    id: 'lesson_004',
    title: 'Risk Management Strategies',
    level: 'INTERMEDIATE',
    duration: '30 min',
    content: `
      Understand risk management:
      - Position sizing
      - Stop-loss orders
      - Risk-reward ratios
      - Money management principles
    `,
    quiz: [
      {
        id: 'q4',
        question: 'What is a stop-loss order used for?',
        options: ['Maximize profits', 'Limit potential losses', 'Increase leverage', 'Reduce fees'],
        correct: 1,
      },
    ],
  },
  {
    id: 'lesson_005',
    title: 'Cryptocurrency Fundamentals',
    level: 'INTERMEDIATE',
    duration: '28 min',
    content: `
      Explore cryptocurrency:
      - Blockchain technology basics
      - Bitcoin vs Ethereum
      - Wallet security
      - Crypto market dynamics
    `,
    quiz: [
      {
        id: 'q5',
        question: 'What is blockchain?',
        options: ['A type of stock', 'A distributed ledger technology', 'A cryptocurrency exchange', 'A trading strategy'],
        correct: 1,
      },
    ],
  },
];

// Mock Macro Data
export const mockMacroData = {
  inflation: 3.4,
  inflationTrend: 'down',
  gdp: 2.5,
  gdpTrend: 'up',
  interestRate: 5.25,
  interestRateTrend: 'stable',
  unemployment: 3.9,
  unemploymentTrend: 'stable',
  lastUpdated: '2024-03-21',
};

// Candlestick Data for Assets (30 days of price data)
export const mockCandleData = {
  AAPL: [
    { date: '2024-02-20', open: 175.50, high: 178.25, low: 174.80, close: 177.30, volume: 52300000 },
    { date: '2024-02-21', open: 177.30, high: 180.10, low: 177.00, close: 179.40, volume: 58900000 },
    { date: '2024-02-22', open: 179.40, high: 182.50, low: 179.20, close: 181.90, volume: 64200000 },
    { date: '2024-02-23', open: 181.90, high: 180.30, low: 179.50, close: 179.80, volume: 49100000 },
    { date: '2024-02-24', open: 179.80, high: 181.20, low: 178.90, close: 180.50, volume: 45600000 },
    { date: '2024-02-26', open: 180.50, high: 182.30, low: 180.10, close: 181.80, volume: 50200000 },
    { date: '2024-02-27', open: 181.80, high: 184.10, low: 181.50, close: 183.60, volume: 55800000 },
    { date: '2024-02-28', open: 183.60, high: 185.20, low: 183.20, close: 184.50, volume: 48900000 },
    { date: '2024-02-29', open: 184.50, high: 186.80, low: 184.30, close: 185.90, volume: 61500000 },
    { date: '2024-03-01', open: 185.90, high: 187.30, low: 185.50, close: 186.80, volume: 52100000 },
  ],
  BTC: [
    { date: '2024-02-20', open: 49500, high: 51200, low: 49300, close: 50800, volume: 2100000000 },
    { date: '2024-02-21', open: 50800, high: 52500, low: 50600, close: 51900, volume: 2400000000 },
    { date: '2024-02-22', open: 51900, high: 53800, low: 51700, close: 52900, volume: 2650000000 },
    { date: '2024-02-23', open: 52900, high: 51500, low: 50200, close: 50800, volume: 1950000000 },
    { date: '2024-02-24', open: 50800, high: 52100, low: 50300, close: 51600, volume: 2050000000 },
    { date: '2024-02-26', open: 51600, high: 53200, low: 51400, close: 52800, volume: 2280000000 },
    { date: '2024-02-27', open: 52800, high: 55100, low: 52600, close: 54300, volume: 2720000000 },
    { date: '2024-02-28', open: 54300, high: 56200, low: 54100, close: 55800, volume: 2890000000 },
    { date: '2024-02-29', open: 55800, high: 57500, low: 55600, close: 57000, volume: 3100000000 },
    { date: '2024-03-01', open: 57000, high: 58200, low: 52300, close: 52300, volume: 3450000000 },
  ],
  SPY: [
    { date: '2024-02-20', open: 465.30, high: 468.50, low: 464.80, close: 467.20, volume: 48900000 },
    { date: '2024-02-21', open: 467.20, high: 470.10, low: 466.90, close: 469.40, volume: 52100000 },
    { date: '2024-02-22', open: 469.40, high: 473.20, low: 469.10, close: 472.50, volume: 58400000 },
    { date: '2024-02-23', open: 472.50, high: 471.30, low: 469.60, close: 470.20, volume: 45200000 },
    { date: '2024-02-24', open: 470.20, high: 472.80, low: 469.50, close: 471.90, volume: 41800000 },
    { date: '2024-02-26', open: 471.90, high: 474.60, low: 471.50, close: 473.80, volume: 49300000 },
    { date: '2024-02-27', open: 473.80, high: 477.20, low: 473.50, close: 476.10, volume: 54700000 },
    { date: '2024-02-28', open: 476.10, high: 479.30, low: 475.90, close: 478.20, volume: 52900000 },
    { date: '2024-02-29', open: 478.20, high: 481.50, low: 478.00, close: 480.60, volume: 59100000 },
    { date: '2024-03-01', open: 480.60, high: 486.50, low: 479.80, close: 485.20, volume: 63200000 },
  ],
};

// Historical Events and News for Assets
export const mockHistoricalEvents = {
  AAPL: [
    {
      date: '2024-02-28',
      event: 'Apple Reports Record Q1 iPhone Sales',
      impact: 'positive',
      description: 'Apple exceeded earnings expectations with strong iPhone 15 demand in Asian markets, driving stock price up 1.8%.',
      category: 'earnings',
    },
    {
      date: '2024-02-25',
      event: 'Market Rally on Soft CPI Data',
      impact: 'positive',
      description: 'Inflation comes in lower than expected, supporting tech sector rally. AAPL benefits from reduced interest rate concerns.',
      category: 'macro',
    },
    {
      date: '2024-02-20',
      event: 'Fed Signals Stable Interest Rates',
      impact: 'neutral',
      description: 'Federal Reserve officials indicate no immediate changes to monetary policy through 2024.',
      category: 'macro',
    },
  ],
  BTC: [
    {
      date: '2024-03-01',
      event: 'Bitcoin Hits New All-Time High',
      impact: 'positive',
      description: 'Bitcoin surges past previous record amid institutional adoption and BlackRock ETF inflows.',
      category: 'crypto',
    },
    {
      date: '2024-02-27',
      event: 'Crypto Market Rally Accelerates',
      impact: 'positive',
      description: 'Strong institutional buying pressure combined with declining inflation signals sustained demand for crypto assets.',
      category: 'macro',
    },
    {
      date: '2024-02-22',
      event: 'SEC Approves Bitcoin Spot ETF',
      impact: 'positive',
      description: 'SEC approval of spot Bitcoin ETF removes major barrier to institutional adoption, driving prices higher.',
      category: 'regulatory',
    },
  ],
  SPY: [
    {
      date: '2024-02-28',
      event: 'Tech Sector Leads Market Gains',
      impact: 'positive',
      description: 'SPY gains 2.3% as mega-cap tech stocks drive market higher on strong earnings.',
      category: 'earnings',
    },
    {
      date: '2024-02-23',
      event: 'Market Volatility Index Declines',
      impact: 'positive',
      description: 'VIX falls below 15 as market sentiment improves, supporting broad market gains.',
      category: 'macro',
    },
    {
      date: '2024-02-20',
      event: 'Fed Powell Speech on Economic Stability',
      impact: 'neutral',
      description: 'Fed Chair Powell comments on economic resilience and stable financial conditions.',
      category: 'macro',
    },
  ],
};

// Asset Analytical Insights
export const mockAssetInsights = {
  AAPL: {
    resistance: 190.50,
    support: 182.00,
    movingAverage50: 181.25,
    movingAverage200: 175.80,
    rsi: 72,
    macd: 'bullish',
    trend: 'uptrend',
    strength: 'strong',
    volatility: 'moderate',
    recommendation: 'Buy on dips',
    analysis: 'Apple is in a strong uptrend with price above both 50-day and 200-day moving averages. RSI indicates overbought conditions, suggesting a potential pullback for better entry points. Support level at $182 is critical.',
  },
  BTC: {
    resistance: 58500,
    support: 50000,
    movingAverage50: 54200,
    movingAverage200: 49300,
    rsi: 78,
    macd: 'bullish',
    trend: 'uptrend',
    strength: 'very strong',
    volatility: 'high',
    recommendation: 'Hold positions',
    analysis: 'Bitcoin shows extreme momentum with RSI above 70. Price is well above both moving averages in a powerful uptrend. Watch for profit-taking near resistance. Long-term trend remains bullish.',
  },
  SPY: {
    resistance: 490.00,
    support: 475.00,
    movingAverage50: 476.50,
    movingAverage200: 468.20,
    rsi: 68,
    macd: 'bullish',
    trend: 'uptrend',
    strength: 'strong',
    volatility: 'moderate',
    recommendation: 'Accumulate',
    analysis: 'SPY is in a healthy uptrend with consistent higher highs and higher lows. Price action above both key moving averages suggests continued strength. Macro backdrop remains supportive for equity markets.',
  },
};

// Helper function to calculate total portfolio value
export const calculatePortfolioMetrics = (holdings) => {
  const totalCost = holdings.reduce((sum, h) => sum + (h.qty * h.buyPrice), 0);
  const totalValue = holdings.reduce((sum, h) => sum + (h.qty * h.currentPrice), 0);
  const totalPnL = totalValue - totalCost;
  const totalPnLPercent = (totalPnL / totalCost) * 100;

  return {
    totalCost,
    totalValue,
    totalPnL,
    totalPnLPercent,
  };
};
