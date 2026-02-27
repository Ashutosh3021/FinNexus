export async function GET() {
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  try {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 3000)

    const res = await fetch(`${backendUrl}/education/stats`, {
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
  return { total_documents: 6, topics_covered: ['Stocks','Technical Analysis','Portfolio'], levels_covered: ['BEGINNER','INTERMEDIATE'] }
}
