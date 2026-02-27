export async function POST(request) {
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  try {
    const body = await request.json()

    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 15000)

    const res = await fetch(`${backendUrl}/education/quiz/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal
    })
    clearTimeout(timeout)

    if (!res.ok) throw new Error(`Backend error: ${res.status}`)
    const data = await res.json()
    const payload = data?.data ?? data
    return Response.json({ success: true, data: payload, source: 'backend' })

  } catch (error) {
    console.warn(`[API] Backend unavailable, using mock data: ${error.message}`)
    return Response.json({ success: true, data: getMockData(), source: 'mock' })
  }
}

function getMockData() {
  return { is_correct: true, explanation: 'Correct — RSI indicates momentum when above 70', xp_earned: 10 }
}
