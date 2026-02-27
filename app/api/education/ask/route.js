export async function POST(request) {
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  try {
    const body = await request.json()

    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 15000)

    const res = await fetch(`${backendUrl}/education/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal
    })
    clearTimeout(timeout)

    if (!res.ok) throw new Error(`Backend error: ${res.status}`)
    const data = await res.json()
    // Unwrap if backend returns { success, data: {...} }
    const payload = data?.data ?? data
    return Response.json({ success: true, data: payload, source: 'backend' })

  } catch (error) {
    console.warn(`[API] Backend unavailable, using mock data: ${error.message}`)
    return Response.json({ success: true, data: getMockData(), source: 'mock' })
  }
}

function getMockData() {
  return {
    explanation: `I'm unable to reach the education service right now. Here's a short summary instead: Stocks represent ownership in companies; prices change based on supply/demand, earnings and macro factors.`,
    analogy: `Think of a stock as a tiny slice of a company pie.`,
    market_example: `Buying 10 shares of AAPL at $150`,
    visual_data: { type: null, title: '', data: [] },
    key_takeaway: 'Start with diversified ETFs if you are new',
    follow_up_questions: ['Show beginner lessons','Explain ETFs'],
    related_playground_scenario: null
  }
}
