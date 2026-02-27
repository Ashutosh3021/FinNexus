export async function GET() {
  try {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const res = await fetch(`${backendUrl}/advisor/context-summary`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!res.ok) {
      console.warn('Backend returned non-OK status for /advisor/context-summary', res.status);
      // Fallback mock context so UI can render
      const fallback = {
        success: false,
        data: {
          portfolio_summary: { summary: 'No portfolio data', holdings_count: 0, total_value: 0, currency: 'INR' },
          prediction_stats: { win_rate: 0, current_streak: 0, total_rounds: 0, recent_results: [], trend: 'declining' },
          news_headlines: [],
          learning_progress: { completed_topics: 0, total_topics: 0, weak_areas: [], current_topic: null }
        },
        error: 'Backend unavailable'
      };
      return Response.json(fallback, { status: 200 });
    }

    const data = await res.json();
    return Response.json(data, { status: 200 });
  } catch (error) {
    console.error('Error fetching advisor context:', error);
    return Response.json(
      { success: false, error: 'Failed to fetch context' },
      { status: 500 }
    );
  }
}
