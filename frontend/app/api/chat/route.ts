import { NextRequest } from 'next/server';
import OpenAI from 'openai';
import { supabase } from '@/lib/supabase';
import { buildChatContext, formatContextForAI } from '@/lib/chat-context';
import {
  buildDobbySystemPrompt,
  detectCrisisIndicators,
} from '@/lib/dobby-system-prompt';

// Initialize OpenAI with fallback error handling
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY || '',
  dangerouslyAllowBrowser: false, // Server-side only
});

// Use the comprehensive system prompt from dobby-system-prompt.ts
const DOBBY_BASE_PROMPT = buildDobbySystemPrompt();

interface ChatRequestBody {
  message: string;
  conversationId?: string;
  sessionId?: string; // Optional: if chatting about specific session
  userId: string; // From auth context
}

/**
 * POST /api/chat
 *
 * Handles streaming chat with GPT-4o, database persistence, and patient context injection
 */
export async function POST(req: NextRequest) {
  console.log('[Chat API] POST request started');
  try {
    console.log('[Chat API] Parsing request body...');
    const body: ChatRequestBody = await req.json();
    const { message, conversationId, sessionId, userId } = body;

    console.log('[Chat API] Request received:', { userId, hasMessage: !!message, conversationId, message: message?.substring(0, 50) });

    if (!message || !userId) {
      return new Response(
        JSON.stringify({ error: 'Missing required fields: message, userId' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Check OpenAI API key
    if (!process.env.OPENAI_API_KEY) {
      console.error('[Chat API] OPENAI_API_KEY not configured');
      return new Response(
        JSON.stringify({ error: 'OpenAI API key not configured' }),
        { status: 500, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // STATELESS MODE: Skip database operations, keep chat working with in-memory state only
    // Enable database mode by setting ENABLE_CHAT_DB_PERSISTENCE=true in .env
    const isStatelessMode = process.env.ENABLE_CHAT_DB_PERSISTENCE !== 'true';
    console.log('[Chat API] Stateless mode (no DB):', isStatelessMode);

    if (isStatelessMode) {
      // Stateless mode: No DB persistence, just OpenAI streaming
      // Chat history is managed client-side (lost on refresh)
      console.log('🔓 Stateless mode: Skipping database, streaming only');

      try {
        const stream = await openai.chat.completions.create({
        model: 'gpt-4o',
        messages: [
          { role: 'system', content: DOBBY_BASE_PROMPT },
          { role: 'user', content: message },
        ],
        temperature: 0.7,
        max_tokens: 1000,
        stream: true,
      });

      const encoder = new TextEncoder();
      const readableStream = new ReadableStream({
        async start(controller) {
          try {
            for await (const chunk of stream) {
              const content = chunk.choices[0]?.delta?.content || '';
              if (content) {
                controller.enqueue(encoder.encode(`data: ${JSON.stringify({ content })}\n\n`));
              }
            }

            controller.enqueue(
              encoder.encode(
                `data: ${JSON.stringify({
                  done: true,
                  conversationId: 'dev-bypass-conversation',
                })}\n\n`
              )
            );

            controller.close();
          } catch (error) {
            console.error('Streaming error:', error);
            controller.error(error);
          }
        },
      });

        return new Response(readableStream, {
          headers: {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
          },
        });
      } catch (bypassError) {
        console.error('[Chat API] Dev bypass error:', bypassError);
        throw bypassError; // Re-throw to be caught by main catch block
      }
    }

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // STEP 1: Usage Tracking (unlimited messages, tracking only)
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    const { error: usageError } = await supabase.rpc(
      'increment_chat_usage',
      { p_user_id: userId }
    );

    if (usageError) {
      console.error('Usage tracking error:', usageError);
      // Continue even if tracking fails - don't block user
    }

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // STEP 2: Get or Create Conversation
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    let activeConversationId = conversationId;

    if (!activeConversationId) {
      // Create new conversation
      const { data: newConversation, error: convError } = await supabase
        .from('chat_conversations')
        .insert({
          user_id: userId,
          session_id: sessionId || null,
          title: 'New Chat', // Will be auto-generated after first exchange
        })
        .select('id')
        .single();

      if (convError || !newConversation) {
        console.error('Failed to create conversation:', convError);
        return new Response(
          JSON.stringify({ error: 'Failed to create conversation' }),
          { status: 500, headers: { 'Content-Type': 'application/json' } }
        );
      }

      activeConversationId = newConversation.id;
    }

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // STEP 3: Save User Message to Database
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    const { error: userMsgError } = await supabase
      .from('chat_messages')
      .insert({
        conversation_id: activeConversationId,
        role: 'user',
        content: message,
        metadata: {
          timestamp: new Date().toISOString(),
        },
      });

    if (userMsgError) {
      console.error('Failed to save user message:', userMsgError);
      return new Response(
        JSON.stringify({ error: 'Failed to save message' }),
        { status: 500, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // STEP 4: Crisis Detection
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    const isCrisisMessage = detectCrisisIndicators(message);

    if (isCrisisMessage) {
      console.log(`[CRISIS DETECTED] User ${userId} - Message contains crisis indicators`);
      // TODO: In future, flag for therapist notification (with permission)
    }

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // STEP 5: Build Patient Context (therapy history, sessions, goals)
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    const context = await buildChatContext(userId, sessionId);
    const contextPrompt = formatContextForAI(context);

    // Add crisis context if detected
    const crisisContext = isCrisisMessage
      ? `\n\n━━━ CRISIS ALERT ━━━\nThis message contains potential crisis indicators. Prioritize safety response per crisis protocol. Be supportive, assess safety, provide resources.\n━━━━━━━━━━━━━━━━━━━━━━`
      : '';

    const systemPrompt = `${DOBBY_BASE_PROMPT}

━━━ PATIENT CONTEXT ━━━
${contextPrompt}
━━━━━━━━━━━━━━━━━━━━━━${crisisContext}`;

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // STEP 6: Load Previous Messages (for conversation history)
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    const { data: previousMessages } = await supabase
      .from('chat_messages')
      .select('role, content')
      .eq('conversation_id', activeConversationId)
      .order('created_at', { ascending: true })
      .limit(20); // Last 20 messages for context

    const chatHistory = previousMessages?.map((msg) => ({
      role: msg.role as 'user' | 'assistant',
      content: msg.content,
    })) || [];

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // STEP 6: Stream GPT-4o Response (word-by-word like ChatGPT)
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    const stream = await openai.chat.completions.create({
      model: 'gpt-4o',
      messages: [
        { role: 'system', content: systemPrompt },
        ...chatHistory,
      ],
      temperature: 0.7,
      max_tokens: 1000,
      stream: true,
    });

    // Create a ReadableStream for Server-Sent Events (SSE)
    let fullResponse = '';

    const encoder = new TextEncoder();
    const readableStream = new ReadableStream({
      async start(controller) {
        try {
          for await (const chunk of stream) {
            const content = chunk.choices[0]?.delta?.content || '';
            if (content) {
              fullResponse += content;
              // Send as Server-Sent Event
              controller.enqueue(encoder.encode(`data: ${JSON.stringify({ content })}\n\n`));
            }
          }

          // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          // STEP 7: Save Assistant Response to Database
          // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          const { error: assistantMsgError } = await supabase
            .from('chat_messages')
            .insert({
              conversation_id: activeConversationId,
              role: 'assistant',
              content: fullResponse,
              metadata: {
                timestamp: new Date().toISOString(),
                model: 'gpt-4o',
                tokens: fullResponse.length / 4, // Rough estimate
              },
            });

          if (assistantMsgError) {
            console.error('Failed to save assistant message:', assistantMsgError);
          }

          // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          // STEP 8: Auto-Generate Conversation Title (first message only)
          // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          const { data: conversation } = await supabase
            .from('chat_conversations')
            .select('message_count, title')
            .eq('id', activeConversationId)
            .single();

          if (conversation && conversation.message_count === 2 && conversation.title === 'New Chat') {
            // Generate title using GPT-4o-mini (cheaper for this task)
            const titleCompletion = await openai.chat.completions.create({
              model: 'gpt-4o-mini',
              messages: [
                {
                  role: 'system',
                  content: 'Generate a short, 3-5 word title for this conversation. Return ONLY the title, nothing else.',
                },
                {
                  role: 'user',
                  content: `User's first message: "${message}"\n\nAssistant's response: "${fullResponse}"`,
                },
              ],
              max_tokens: 20,
              temperature: 0.7,
            });

            const generatedTitle = titleCompletion.choices[0]?.message?.content?.trim() || 'New Chat';

            await supabase
              .from('chat_conversations')
              .update({ title: generatedTitle })
              .eq('id', activeConversationId);
          }

          // Send completion event
          controller.enqueue(
            encoder.encode(
              `data: ${JSON.stringify({
                done: true,
                conversationId: activeConversationId,
              })}\n\n`
            )
          );

          controller.close();
        } catch (error) {
          console.error('Streaming error:', error);
          controller.error(error);
        }
      },
    });

    return new Response(readableStream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  } catch (error) {
    console.error('[Chat API] Fatal error:', error);
    console.error('[Chat API] Error details:', {
      name: error instanceof Error ? error.name : 'Unknown',
      message: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined,
    });
    return new Response(
      JSON.stringify({
        error: 'Internal server error',
        message: error instanceof Error ? error.message : "I'm having trouble responding right now. Please try again in a moment.",
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
}
