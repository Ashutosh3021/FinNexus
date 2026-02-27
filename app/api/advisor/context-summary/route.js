export async function GET() {
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  try {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 3000)

    const res = await fetch(`${backendUrl}/advisor/context-summary`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal
    })
    clearTimeout(timeout)

    if (!res.ok) throw new Error(`Backend error: ${res.status}`)
    const data = await res.json()
    return Response.json({ success: true, data, source: 'backend' })

  } catch (error) {
    console.warn(`[API] Backend unavailable, using mock data: ${error.message}`)
    return Response.json({ success: true, data: getMockData(), source: 'mock' })
  }
}

function getMockData() {
  return {
    portfolio: {
      totalValue: 124500,
      totalPnl: 24500,
      pnlPercent: 24.5,
      topHolding: 'BTC-USD',
      riskScore: 7,
      riskLabel: 'high',
      allocation: [
        { name: 'Stocks', value: 40, color: '#3B82F6' },
        { name: 'Crypto', value: 30, color: '#F59E0B' },
        { name: 'Gold', value: 15, color: '#EAB308' },
        { name: 'Index', value: 15, color: '#10B981' }
      ]
    },
    predictions: {
      winRate: 62.5,
      totalRounds: 8,
      streak: 2,
      recentResults: ['win','win','loss','win','win']
    },
    learning: {
      progressPercent: 45,
      completedTopics: ['What is Stock Market','P/E Ratio','RSI','Bull vs Bear'],
      weakTopics: ['Bollinger Bands', 'Sharpe Ratio'],
      currentTopic: 'How Interest Rates Affect Markets'
    },
    news: [
      { headline: 'Fed holds rates steady at 5.25%', sentiment: 'neutral', category: 'Central Bank' },
      { headline: 'Bitcoin ETF sees record $500M inflows', sentiment: 'positive', category: 'Crypto' },
      { headline: 'NIFTY hits all-time high above 22,000', sentiment: 'positive', category: 'Stock' }
    ]
  }
}
