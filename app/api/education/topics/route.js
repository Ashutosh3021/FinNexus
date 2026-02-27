export async function GET() {
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  try {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 15000)

    const res = await fetch(`${backendUrl}/education/topics`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal
    })
    clearTimeout(timeout)

    if (!res.ok) throw new Error(`Backend error: ${res.status}`)
    const data = await res.json()
    // Normalize to { BEGINNER: [titles], INTERMEDIATE: [...], ADVANCED: [...] }
    const raw = data?.data?.topics ?? data
    let topicsByLevel = {}
    if (Array.isArray(raw)) {
      // Older backend response: array of topic items with level & title
      for (const item of raw) {
        const lvl = String(item.level || '').toUpperCase()
        if (!lvl) continue
        topicsByLevel[lvl] = topicsByLevel[lvl] || []
        topicsByLevel[lvl].push(item.title || item.topic)
      }
    } else if (raw && typeof raw === 'object') {
      for (const [lvl, arr] of Object.entries(raw)) {
        topicsByLevel[lvl] = (arr || []).map((t) => t.title || t.topic || t)
      }
    }
    return Response.json({ success: true, data: topicsByLevel, source: 'backend' })

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
