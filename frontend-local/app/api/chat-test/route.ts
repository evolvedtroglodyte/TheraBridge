import { NextRequest } from 'next/server';

/**
 * Simple test endpoint to verify OpenAI connection
 */
export async function GET(req: NextRequest) {
  const hasKey = !!process.env.OPENAI_API_KEY;
  const keyPrefix = process.env.OPENAI_API_KEY?.slice(0, 10);

  return Response.json({
    openai_configured: hasKey,
    key_prefix: keyPrefix,
    env: process.env.NODE_ENV,
  });
}

export async function POST(req: NextRequest) {
  try {
    const { message } = await req.json();

    return new Response(
      `data: ${JSON.stringify({ content: 'Test response: ' })}\n\n` +
      `data: ${JSON.stringify({ content: message })}\n\n` +
      `data: ${JSON.stringify({ done: true, conversationId: 'test' })}\n\n`,
      {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
        },
      }
    );
  } catch (error) {
    return Response.json({ error: String(error) }, { status: 500 });
  }
}
