export async function POST(request) {
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  try {
    const body = await request.json()

    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 3000)

    const res = await fetch(`${backendUrl}/advisor/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
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
    reply: "I'm temporarily unable to reach the advisor service. Try again shortly.",
    suggested_actions: [
      { label: 'View Portfolio', route: '/portfolio', icon: '📊' },
      { label: 'Learn', route: '/learn', icon: '📚' }
    ],
    related_module: null,
    proactive_insight: null
  }
}
