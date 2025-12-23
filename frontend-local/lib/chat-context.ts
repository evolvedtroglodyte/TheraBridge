/**
 * Chat Context System - Enhanced for Medical AI Companion
 *
 * Builds intelligent context for Dobby by pulling patient's complete therapy journey:
 * - User profile (name, role, therapist info)
 * - ALL therapy sessions (transcripts, summaries, notes, mood patterns)
 * - Treatment goals with progress tracking
 * - Learned techniques and coping strategies
 * - Key insights and breakthroughs
 * - Mood trends over time
 *
 * Smart token management: summarizes old data to stay under GPT-4o limits
 */

import { supabase } from './supabase';
import type { User, TherapySession, TreatmentGoal } from './supabase';

export interface ChatContext {
  user: {
    name: string;
    firstName: string;
    role: string;
    therapistName?: string;
  };
  sessions: {
    count: number;
    recent: TherapySession[];
    summary: string;
    // Enhanced analytics
    topTopics: string[];
    learnedTechniques: string[];
    moodTrend: 'improving' | 'stable' | 'declining' | 'variable' | 'unknown';
    averageMood: string;
    keyInsights: string[];
  };
  goals: TreatmentGoal[];
  timeline: {
    milestones: number;
    recentEvents: string[];
    daysInTherapy: number;
  };
  currentSession?: TherapySession;
}

/**
 * Build context for AI chat
 * @param userId - User ID from database (NOT auth_id)
 * @param sessionId - Optional: if viewing a specific session
 */
export async function buildChatContext(
  userId: string,
  sessionId?: string
): Promise<ChatContext> {
  try {
    // 1. Get user profile with therapist info
    const { data: user } = await supabase
      .from('users')
      .select('first_name, last_name, role')
      .eq('id', userId)
      .single();

    if (!user) {
      throw new Error('User not found');
    }

    // 2. Get therapist name (if patient has one assigned)
    let therapistName: string | undefined;
    const { data: patientData } = await supabase
      .from('patients')
      .select('therapist_id')
      .eq('user_id', userId)
      .single();

    if (patientData?.therapist_id) {
      const { data: therapist } = await supabase
        .from('users')
        .select('first_name, last_name')
        .eq('id', patientData.therapist_id)
        .single();

      if (therapist) {
        therapistName = `${therapist.first_name} ${therapist.last_name}`;
      }
    }

    // 3. Get ALL therapy sessions (sorted newest first)
    const { data: sessions } = await supabase
      .from('therapy_sessions')
      .select('*')
      .eq('patient_id', userId)
      .order('session_date', { ascending: false });

    // 4. Get active treatment goals
    const { data: goals } = await supabase
      .from('treatment_goals')
      .select('*')
      .eq('patient_id', userId)
      .in('status', ['active', 'completed'])
      .order('created_at', { ascending: false });

    // 5. Get current session if specified
    let currentSession: TherapySession | undefined;
    if (sessionId) {
      const { data: session } = await supabase
        .from('therapy_sessions')
        .select('*')
        .eq('id', sessionId)
        .single();

      currentSession = session || undefined;
    }

    // 6. Build enhanced analytics
    const sessionAnalytics = analyzeSessionHistory(sessions || []);

    // 7. Calculate days in therapy
    const daysInTherapy = sessions && sessions.length > 0
      ? Math.floor(
          (Date.now() - new Date(sessions[sessions.length - 1].session_date).getTime()) /
          (1000 * 60 * 60 * 24)
        )
      : 0;

    // 8. Build context object
    const context: ChatContext = {
      user: {
        name: `${user.first_name} ${user.last_name}`,
        firstName: user.first_name,
        role: user.role,
        therapistName,
      },
      sessions: {
        count: sessions?.length || 0,
        recent: sessions?.slice(0, 5) || [],
        summary: buildSessionSummary(sessions || []),
        ...sessionAnalytics,
      },
      goals: goals || [],
      timeline: {
        milestones: countMilestones(sessions || []),
        recentEvents: extractRecentEvents(sessions || []),
        daysInTherapy,
      },
      currentSession,
    };

    return context;
  } catch (error) {
    console.error('Error building chat context:', error);
    throw error;
  }
}

/**
 * Analyze session history for patterns and insights
 */
function analyzeSessionHistory(sessions: TherapySession[]): {
  topTopics: string[];
  learnedTechniques: string[];
  moodTrend: 'improving' | 'stable' | 'declining' | 'variable' | 'unknown';
  averageMood: string;
  keyInsights: string[];
} {
  if (sessions.length === 0) {
    return {
      topTopics: [],
      learnedTechniques: [],
      moodTrend: 'unknown',
      averageMood: 'unknown',
      keyInsights: [],
    };
  }

  // Count topic frequency
  const topicCounts: Record<string, number> = {};
  const techniqueCounts: Record<string, number> = {};
  const moods: string[] = [];
  const allInsights: string[] = [];

  sessions.forEach((session) => {
    // Topics
    session.topics?.forEach((topic) => {
      topicCounts[topic] = (topicCounts[topic] || 0) + 1;
    });

    // Moods
    if (session.mood) {
      moods.push(session.mood);
    }

    // Key insights
    session.key_insights?.forEach((insight) => {
      allInsights.push(insight);
    });

    // Extract techniques from action items or topics (heuristic)
    const techniqueKeywords = ['breathing', 'grounding', 'TIPP', 'mindfulness', 'journaling',
      'meditation', 'relaxation', 'cognitive', 'thought record', 'opposite action'];

    const sessionText = [
      ...(session.topics || []),
      ...(session.action_items || []),
      session.summary || '',
    ].join(' ').toLowerCase();

    techniqueKeywords.forEach((technique) => {
      if (sessionText.includes(technique.toLowerCase())) {
        techniqueCounts[technique] = (techniqueCounts[technique] || 0) + 1;
      }
    });
  });

  // Sort topics by frequency
  const topTopics = Object.entries(topicCounts)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5)
    .map(([topic]) => topic);

  // Get learned techniques
  const learnedTechniques = Object.keys(techniqueCounts).slice(0, 5);

  // Calculate mood trend (compare first half to second half)
  const moodTrend = calculateMoodTrend(moods);

  // Most common mood
  const moodCounts: Record<string, number> = {};
  moods.forEach((mood) => {
    moodCounts[mood] = (moodCounts[mood] || 0) + 1;
  });
  const averageMood = Object.entries(moodCounts)
    .sort(([, a], [, b]) => b - a)[0]?.[0] || 'unknown';

  // Most recent key insights (last 5)
  const keyInsights = allInsights.slice(0, 5);

  return {
    topTopics,
    learnedTechniques,
    moodTrend,
    averageMood,
    keyInsights,
  };
}

/**
 * Calculate mood trend based on recent vs older sessions
 */
function calculateMoodTrend(
  moods: string[]
): 'improving' | 'stable' | 'declining' | 'variable' | 'unknown' {
  if (moods.length < 3) return 'unknown';

  // Simple mood scoring (you can customize this)
  const moodScores: Record<string, number> = {
    'great': 5,
    'good': 4,
    'positive': 4,
    'hopeful': 4,
    'neutral': 3,
    'okay': 3,
    'mixed': 3,
    'difficult': 2,
    'anxious': 2,
    'low': 2,
    'struggling': 1,
    'crisis': 0,
  };

  const scores = moods.map((mood) => moodScores[mood.toLowerCase()] ?? 3);

  // Compare first half average to second half average
  const midpoint = Math.floor(scores.length / 2);
  const recentAvg = scores.slice(0, midpoint).reduce((a, b) => a + b, 0) / midpoint;
  const olderAvg = scores.slice(midpoint).reduce((a, b) => a + b, 0) / (scores.length - midpoint);

  const diff = recentAvg - olderAvg;

  if (Math.abs(diff) < 0.3) return 'stable';
  if (diff > 0.5) return 'improving';
  if (diff < -0.5) return 'declining';
  return 'variable';
}

/**
 * Count milestone sessions (e.g., sessions marked as breakthroughs)
 */
function countMilestones(sessions: TherapySession[]): number {
  // Count sessions with significant insights or marked as milestones
  return sessions.filter((s) =>
    (s.key_insights && s.key_insights.length >= 2) ||
    s.mood === 'great' ||
    s.mood === 'breakthrough'
  ).length;
}

/**
 * Extract recent significant events from sessions
 */
function extractRecentEvents(sessions: TherapySession[]): string[] {
  const events: string[] = [];

  sessions.slice(0, 5).forEach((session) => {
    if (session.summary) {
      // Extract first sentence as event summary
      const firstSentence = session.summary.split(/[.!?]/)[0];
      if (firstSentence && firstSentence.length > 10) {
        events.push(firstSentence);
      }
    }
  });

  return events.slice(0, 3);
}

/**
 * Build a summary of all sessions for context
 * Keeps token count reasonable by aggregating insights
 */
function buildSessionSummary(sessions: TherapySession[]): string {
  if (sessions.length === 0) {
    return 'No therapy sessions yet.';
  }

  // Extract key info from all sessions
  const allTopics = new Set<string>();
  const allStrategies = new Set<string>();
  const moodCounts: Record<string, number> = {};

  sessions.forEach((session) => {
    // Collect topics
    session.topics?.forEach((topic) => allTopics.add(topic));

    // Collect strategies (if available in session data)
    // session.strategies?.forEach((strategy) => allStrategies.add(strategy));

    // Count moods
    if (session.mood) {
      moodCounts[session.mood] = (moodCounts[session.mood] || 0) + 1;
    }
  });

  // Build summary
  const topicsList = Array.from(allTopics).slice(0, 10).join(', ');
  const mostCommonMood = Object.entries(moodCounts)
    .sort(([, a], [, b]) => b - a)[0]?.[0] || 'unknown';

  return `Patient has completed ${sessions.length} therapy sessions. Common topics: ${topicsList}. Most common mood: ${mostCommonMood}.`;
}

/**
 * Format context for AI system prompt
 * Converts structured data into rich, personalized context for Dobby
 */
export function formatContextForAI(context: ChatContext): string {
  const parts: string[] = [];

  // ═══════════════════════════════════════════════════════════════════════════
  // PATIENT IDENTITY
  // ═══════════════════════════════════════════════════════════════════════════
  parts.push(`━━━ PATIENT PROFILE ━━━`);
  parts.push(`Name: ${context.user.name} (use "${context.user.firstName}" in conversation)`);
  parts.push(`Role: ${context.user.role}`);
  if (context.user.therapistName) {
    parts.push(`Therapist: ${context.user.therapistName}`);
  }
  if (context.timeline.daysInTherapy > 0) {
    parts.push(`Therapy Journey: ${context.timeline.daysInTherapy} days (${context.sessions.count} sessions)`);
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // THERAPY OVERVIEW
  // ═══════════════════════════════════════════════════════════════════════════
  if (context.sessions.count > 0) {
    parts.push(`\n━━━ THERAPY OVERVIEW ━━━`);
    parts.push(context.sessions.summary);

    // Mood trend
    if (context.sessions.moodTrend !== 'unknown') {
      const trendDescriptions = {
        improving: 'Mood has been trending upward recently - acknowledge this progress!',
        stable: 'Mood has been consistent - good stability.',
        declining: 'Mood may be declining - be extra supportive and check in gently.',
        variable: 'Mood has been variable - normalize that healing isn\'t linear.',
      };
      parts.push(`Mood Trend: ${trendDescriptions[context.sessions.moodTrend]}`);
    }

    // Top topics (what they're working on)
    if (context.sessions.topTopics.length > 0) {
      parts.push(`Core Focus Areas: ${context.sessions.topTopics.join(', ')}`);
    }

    // Techniques they've learned
    if (context.sessions.learnedTechniques.length > 0) {
      parts.push(`Techniques in Toolkit: ${context.sessions.learnedTechniques.join(', ')}`);
      parts.push(`(Reference these when relevant - they already know the basics!)`);
    }

    // Key insights from their journey
    if (context.sessions.keyInsights.length > 0) {
      parts.push(`\nRecent Insights from Sessions:`);
      context.sessions.keyInsights.slice(0, 3).forEach((insight, i) => {
        parts.push(`  ${i + 1}. "${insight}"`);
      });
    }

    // Milestones
    if (context.timeline.milestones > 0) {
      parts.push(`\nMilestones Achieved: ${context.timeline.milestones} breakthrough sessions`);
    }
  } else {
    parts.push(`\n━━━ NEW PATIENT ━━━`);
    parts.push(`This patient hasn't had any recorded therapy sessions yet.`);
    parts.push(`Focus on: Building rapport, understanding their goals, explaining how you can help.`);
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // RECENT SESSIONS WITH FULL TRANSCRIPTS
  // ═══════════════════════════════════════════════════════════════════════════
  if (context.sessions.recent.length > 0) {
    parts.push(`\n━━━ RECENT SESSIONS ━━━`);
    context.sessions.recent.forEach((session, i) => {
      const date = new Date(session.session_date).toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
      });
      const topics = session.topics?.slice(0, 3).join(', ') || 'General session';
      const mood = session.mood ? ` | Mood: ${session.mood}` : '';
      parts.push(`  ${i + 1}. ${date} - ${topics}${mood}`);

      // Include full transcript for recent sessions (most recent 3)
      if (i < 3 && session.transcript && Array.isArray(session.transcript)) {
        parts.push(`     ═══ FULL TRANSCRIPT ═══`);
        session.transcript.forEach((segment: any) => {
          const speaker = segment.speaker || 'Unknown';
          const text = segment.text || '';
          parts.push(`     ${speaker}: ${text}`);
        });
        parts.push(`     ═══ END TRANSCRIPT ═══`);
      }

      // Include summary for context
      if (session.summary) {
        parts.push(`     Summary: ${session.summary}`);
      }

      // Include action items for recent sessions
      if (i < 2 && session.action_items && session.action_items.length > 0) {
        parts.push(`     Homework: ${session.action_items.slice(0, 2).join('; ')}`);
      }
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // TREATMENT GOALS
  // ═══════════════════════════════════════════════════════════════════════════
  if (context.goals.length > 0) {
    parts.push(`\n━━━ TREATMENT GOALS ━━━`);
    const activeGoals = context.goals.filter((g) => g.status === 'active');
    const completedGoals = context.goals.filter((g) => g.status === 'completed');

    if (activeGoals.length > 0) {
      parts.push(`Active Goals:`);
      activeGoals.forEach((goal) => {
        const progressBar = getProgressBar(goal.progress);
        parts.push(`  • ${goal.title} ${progressBar} ${goal.progress}%`);
        if (goal.description) {
          parts.push(`    ${goal.description.slice(0, 100)}`);
        }
      });
    }

    if (completedGoals.length > 0) {
      parts.push(`Completed Goals: ${completedGoals.map((g) => g.title).join(', ')}`);
      parts.push(`(Celebrate these achievements when relevant!)`);
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // CURRENT SESSION CONTEXT (if viewing specific session)
  // ═══════════════════════════════════════════════════════════════════════════
  if (context.currentSession) {
    parts.push(`\n━━━ CURRENT VIEWING CONTEXT ━━━`);
    const sessionDate = new Date(context.currentSession.session_date).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
    parts.push(`${context.user.firstName} is reviewing their session from ${sessionDate}.`);

    // Include full transcript of current session
    if (context.currentSession.transcript && Array.isArray(context.currentSession.transcript)) {
      parts.push(`\n═══ FULL SESSION TRANSCRIPT ═══`);
      context.currentSession.transcript.forEach((segment: any) => {
        const speaker = segment.speaker || 'Unknown';
        const text = segment.text || '';
        parts.push(`${speaker}: ${text}`);
      });
      parts.push(`═══ END TRANSCRIPT ═══\n`);
    }

    if (context.currentSession.summary) {
      parts.push(`Session Summary: ${context.currentSession.summary}`);
    }
    if (context.currentSession.topics && context.currentSession.topics.length > 0) {
      parts.push(`Topics Discussed: ${context.currentSession.topics.join(', ')}`);
    }
    if (context.currentSession.mood) {
      parts.push(`Session Mood: ${context.currentSession.mood}`);
    }
    if (context.currentSession.key_insights && context.currentSession.key_insights.length > 0) {
      parts.push(`Key Insights: ${context.currentSession.key_insights.join('; ')}`);
    }
    if (context.currentSession.action_items && context.currentSession.action_items.length > 0) {
      parts.push(`Action Items: ${context.currentSession.action_items.join('; ')}`);
    }

    parts.push(`\nWhen ${context.user.firstName} says "this session" or "today's session", they mean the one above.`);
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // INTERACTION GUIDANCE
  // ═══════════════════════════════════════════════════════════════════════════
  parts.push(`\n━━━ INTERACTION GUIDANCE ━━━`);
  parts.push(`• Use "${context.user.firstName}" occasionally for warmth`);
  if (context.user.therapistName) {
    parts.push(`• Refer to their therapist as "${context.user.therapistName}" when relevant`);
  }
  if (context.sessions.learnedTechniques.length > 0) {
    parts.push(`• They know: ${context.sessions.learnedTechniques.join(', ')} - build on this foundation`);
  }
  if (context.sessions.topTopics.length > 0) {
    parts.push(`• Their focus areas: ${context.sessions.topTopics.join(', ')} - these are sensitive topics`);
  }

  return parts.join('\n');
}

/**
 * Create a simple progress bar for goals
 */
function getProgressBar(progress: number): string {
  const filled = Math.round(progress / 10);
  const empty = 10 - filled;
  return `[${'█'.repeat(filled)}${'░'.repeat(empty)}]`;
}

/**
 * Estimate token count for context
 * Rough estimate: 1 token ≈ 4 characters
 */
export function estimateTokenCount(text: string): number {
  return Math.ceil(text.length / 4);
}
