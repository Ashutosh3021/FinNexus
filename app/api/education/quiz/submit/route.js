export async function POST(request) {
  try {
    const body = await request.json();
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    const res = await fetch(`${backendUrl}/education/quiz/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      console.warn('Backend returned non-OK status for /education/quiz/submit', res.status);
      return Response.json({ success: false, data: { is_correct: false, explanation: 'Service unavailable', xp_earned: 0 }, error: 'Backend unavailable' }, { status: 200 });
    }

    const data = await res.json();
    return Response.json(data, { status: 200 });
  } catch (error) {
    console.error('Error submitting quiz:', error);
    return Response.json(
      { success: false, error: 'Failed to submit quiz answer' },
      { status: 500 }
    );
  }
}
