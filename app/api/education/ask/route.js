export async function POST(request) {
  try {
    const body = await request.json();
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    const res = await fetch(`${backendUrl}/education/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      console.warn('Backend returned non-OK status for /education/ask', res.status);
      // Graceful fallback: return a minimal lesson-like structure
      const fallback = {
        success: false,
        data: {
          explanation: `Sorry, education service is temporarily unavailable.`,
          analogy: null,
          market_example: null,
          visual_data: { type: null, title: '', data: [] },
          key_takeaway: 'Service unavailable',
          follow_up_questions: [],
          related_playground_scenario: null
        },
        error: 'Backend unavailable'
      };
      return Response.json(fallback, { status: 200 });
    }

    const data = await res.json();
    return Response.json(data, { status: 200 });
  } catch (error) {
    console.error('Error asking question:', error);
    return Response.json(
      { success: false, error: 'Failed to process question' },
      { status: 500 }
    );
  }
}
