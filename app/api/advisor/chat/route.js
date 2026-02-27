export async function POST(request) {
  try {
    const body = await request.json();
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    const res = await fetch(`${backendUrl}/advisor/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      console.warn('Backend returned non-OK status for /advisor/chat', res.status);
      const fallback = {
        success: false,
        data: {
          reply: "I'm temporarily unable to reach the advisor service. Try again shortly.",
          suggested_actions: [
            { label: 'View Portfolio', route: '/portfolio', icon: '📊' },
            { label: 'Learn', route: '/learn', icon: '📚' }
          ],
          related_module: null,
          proactive_insight: null
        },
        error: 'Backend unavailable'
      };
      return Response.json(fallback, { status: 200 });
    }

    const data = await res.json();
    return Response.json(data, { status: 200 });
  } catch (error) {
    console.error('Error calling advisor chat:', error);
    return Response.json(
      { success: false, error: 'Failed to process advisor request' },
      { status: 500 }
    );
  }
}
