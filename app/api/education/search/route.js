export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const query = searchParams.get('q');
    const level = searchParams.get('level') || 'BEGINNER';
    
    if (!query) {
      return Response.json(
        { success: false, error: 'Query parameter required' },
        { status: 400 }
      );
    }

    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const res = await fetch(
      `${backendUrl}/education/search?q=${encodeURIComponent(query)}&level=${encodeURIComponent(level)}`,
      { method: 'GET', headers: { 'Content-Type': 'application/json' } }
    );

    if (!res.ok) {
      console.warn('Backend returned non-OK status for /education/search', res.status);
      return Response.json({ success: false, data: [], error: 'Backend unavailable' }, { status: 200 });
    }

    const data = await res.json();
    return Response.json(data, { status: 200 });
  } catch (error) {
    console.error('Error searching lessons:', error);
    return Response.json(
      { success: false, error: 'Failed to search lessons' },
      { status: 500 }
    );
  }
}
