export async function GET() {
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  try {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 3000)

    const res = await fetch(`${backendUrl}/education/topics`, {
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
    return Response.json({
      success: true,
      data: getMockData(),
      source: 'mock'
    })
  }
}

function getMockData() {
  return [
    { id: 1, slug: 'stock-market-basics', title: 'What is Stock Market', level: 'beginner', estimatedTime: '5 min', completed: true },
    { id: 2, slug: 'pe-ratio', title: 'P/E Ratio Explained', level: 'intermediate', estimatedTime: '8 min', completed: true },
    { id: 3, slug: 'rsi-indicator', title: 'RSI Indicator', level: 'intermediate', estimatedTime: '10 min', completed: false },
    { id: 4, slug: 'macd', title: 'MACD Indicator', level: 'intermediate', estimatedTime: '10 min', completed: false },
    { id: 5, slug: 'sharpe-ratio', title: 'Sharpe Ratio', level: 'advanced', estimatedTime: '12 min', completed: false },
    { id: 6, slug: 'interest-rates', title: 'How Interest Rates Affect Markets', level: 'intermediate', estimatedTime: '9 min', completed: false }
  ]
}
