import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

const DOBBY_SYSTEM_PROMPT = `You are Dobby, a friendly and supportive AI therapy companion. Your role is to:

1. Help users prepare for their therapy sessions
2. Answer questions about therapeutic techniques (like TIPP, grounding exercises, breathing techniques, etc.)
3. Provide emotional support and validation
4. Help track mood patterns and insights
5. Forward messages to their therapist when requested

Guidelines:
- Be warm, empathetic, and non-judgmental
- Use simple, clear language
- Validate feelings before offering suggestions
- Never provide medical diagnoses or replace professional therapy
- If someone is in crisis, encourage them to contact their therapist or crisis hotline
- Keep responses concise but helpful (2-4 sentences typically)
- Reference their therapy journey when relevant
- Maintain a calm, supportive tone

Remember: Everything shared is confidential and designed to support their therapy journey.`;

const THERAPIST_MODE_PROMPT = `You are helping forward a message to the user's therapist. When in therapist mode:
- Confirm you've received their message
- Let them know their therapist typically responds within 24 hours
- Ask if there's anything else you can help with in the meantime
- If the message seems urgent, gently suggest they could also call their therapist directly`;

export async function POST(req: NextRequest) {
  try {
    const { messages, mode } = await req.json();

    if (!messages || !Array.isArray(messages)) {
      return NextResponse.json(
        { error: 'Invalid messages format' },
        { status: 400 }
      );
    }

    const systemPrompt = mode === 'therapist' ? THERAPIST_MODE_PROMPT : DOBBY_SYSTEM_PROMPT;

    const completion = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        { role: 'system', content: systemPrompt },
        ...messages,
      ],
      max_tokens: 500,
      temperature: 0.7,
    });

    const responseMessage = completion.choices[0]?.message?.content ||
      "I'm here to help. Could you tell me more about what's on your mind?";

    return NextResponse.json({ message: responseMessage });
  } catch (error) {
    console.error('OpenAI API error:', error);

    // Return a fallback response instead of an error
    return NextResponse.json({
      message: "I understand you're reaching out. While I'm having a moment of technical difficulty, I want you to know I'm here for you. Could you try again in a moment?",
    });
  }
}
