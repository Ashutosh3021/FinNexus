export async function GET(request, { params }) {
  try {
    const { topic_slug } = params;
    const { searchParams } = new URL(request.url);
    const level = searchParams.get('level') || 'BEGINNER';

    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    const res = await fetch(`${backendUrl}/education/lesson/${encodeURIComponent(topic_slug)}?level=${encodeURIComponent(level)}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal
    });
    clearTimeout(timeout);

    if (!res.ok) {
      console.warn('Backend returned non-OK status for /education/lesson', res.status);
      return Response.json({ success: false, data: { title: topic_slug, content: 'Lesson service unavailable' }, error: 'Backend unavailable' }, { status: 200 });
    }

    const data = await res.json();
    const payload = data?.data ?? data;
    return Response.json({ success: true, data: payload }, { status: 200 });
  } catch (error) {
    console.error('Error fetching lesson:', error);
    return Response.json(
      { success: false, error: 'Failed to fetch lesson' },
      { status: 500 }
    );
  }
}
