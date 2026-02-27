export async function GET() {
  try {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const res = await fetch(`${backendUrl}/education/stats`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!res.ok) {
      console.warn('Backend returned non-OK status for /education/stats', res.status);
      return Response.json({ success: false, data: { total_documents: 0, topics_covered: [], levels_covered: [] }, error: 'Backend unavailable' }, { status: 200 });
    }

    const data = await res.json();
    return Response.json(data, { status: 200 });
  } catch (error) {
    console.error('Error fetching stats:', error);
    return Response.json(
      { success: false, error: 'Failed to fetch stats' },
      { status: 500 }
    );
  }
}
