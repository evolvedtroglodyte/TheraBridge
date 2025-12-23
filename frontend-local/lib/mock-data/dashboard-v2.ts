/**
 * Dashboard V2 Mock Data
 *
 * Comprehensive mock data for all 7 dashboard widgets matching
 * PAGE_LAYOUT_ARCHITECTURE.md specifications.
 *
 * Data covers 10 therapy sessions from Dec 17 to Oct 15
 * with realistic therapy-appropriate content.
 */

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

/** Notes/Goals - AI-generated journey summary */
export interface NotesGoalsCompact {
  sessionCount: number;
  bullets: string[];
  currentFocus: string[];
}

export interface NotesGoalsSection {
  title: string;
  content: string;
  isCollapsed: boolean;
}

export interface NotesGoalsExpanded {
  title: string;
  sections: NotesGoalsSection[];
}

export interface NotesGoalsData {
  compact: NotesGoalsCompact;
  expanded: NotesGoalsExpanded;
}

/** AI Chat - Dynamic prompts */
export interface AIChatPrompt {
  id: string;
  text: string;
  priority: number; // 1 = highest
  category: 'session-prep' | 'mood-insight' | 'homework' | 'therapist-communication' | 'pattern-exploration';
}

export interface AIChatData {
  prompts: AIChatPrompt[];
  description: string;
  expandedDescription: {
    title: string;
    capabilities: string[];
  };
}

/** To-Do - Homework tasks */
export interface ToDoTask {
  id: string;
  text: string;
  completed: boolean;
  sourceSession: string;
  createdAt: string;
}

export interface ToDoData {
  active: ToDoTask[];
  completed: ToDoTask[];
}

/** Progress Patterns - 4 carousel pages of data */
export interface MoodTrendPoint {
  session: number;
  date: string;
  mood: number; // 1-10 scale
}

export interface HomeworkImpactWeek {
  week: string;
  startDate: string;
  endDate: string;
  completionRate: number; // 0-100
  averageMood: number; // 1-10
}

export interface SessionConsistencyDay {
  date: string;
  hasSession: boolean;
  dayOfWeek: number; // 0 = Sunday
}

export interface StrategyEffectiveness {
  strategy: string;
  timesUsed: number;
  moodCorrelation: number; // -1 to 1, where 1 = strong positive correlation
  description: string;
}

export interface ProgressPatternsData {
  moodTrend: {
    data: MoodTrendPoint[];
    insight: string;
    improvement: number; // percentage
  };
  homeworkImpact: {
    data: HomeworkImpactWeek[];
    insight: string;
    correlation: string;
  };
  sessionConsistency: {
    data: SessionConsistencyDay[];
    insight: string;
    averageDaysBetween: number;
  };
  strategyEffectiveness: {
    data: StrategyEffectiveness[];
    insight: string;
    topStrategy: string;
  };
}

/** Therapist Bridge - Connection prompts */
export interface TherapistBridgeItem {
  id: string;
  text: string;
  context?: string;
}

export interface TherapistBridgeSection {
  title: string;
  items: TherapistBridgeItem[];
}

export interface TherapistBridgeData {
  compact: {
    conversationStarters: TherapistBridgeItem;
    shareProgress: TherapistBridgeItem;
    sessionPrep: TherapistBridgeItem;
  };
  expanded: {
    conversationStarters: TherapistBridgeSection;
    shareProgress: TherapistBridgeSection;
    sessionPrep: TherapistBridgeSection;
    nextSessionDate: string;
  };
}

/** Sessions - 10 therapy sessions */
export type SessionMood = 'positive' | 'neutral' | 'low';

export interface SessionAction {
  id: string;
  text: string;
}

export interface Session {
  id: string;
  sessionNumber: number;
  date: string;
  displayDate: string; // "Dec 17" format
  duration: number; // minutes
  mood: SessionMood;
  moodEmoji: string;
  topics: string[];
  strategy: string;
  strategyDescription?: string;
  actions: SessionAction[];
  isMilestone: boolean;
  milestoneText?: string;
  transcript: string;
  summary: string;
}

/** Timeline - Derived from sessions */
export interface TimelineEntry {
  id: string;
  sessionId: string;
  date: string;
  displayDate: string;
  topicPreview: string;
  mood: SessionMood;
  moodColor: string;
  isMilestone: boolean;
  milestoneText?: string;
}

/** Complete Dashboard Data */
export interface DashboardV2Data {
  notesGoals: NotesGoalsData;
  aiChat: AIChatData;
  toDo: ToDoData;
  progressPatterns: ProgressPatternsData;
  therapistBridge: TherapistBridgeData;
  sessions: Session[];
  timeline: TimelineEntry[];
}

// ============================================================================
// MOCK DATA
// ============================================================================

/** Notes/Goals Widget Data */
export const notesGoalsData: NotesGoalsData = {
  compact: {
    sessionCount: 10,
    bullets: [
      "Reduced depression symptoms by 67% (PHQ-9: 18 to 6)",
      "Mastered 3 coping strategies: grounding, breathing, laddering",
      "Core pattern identified: work stress triggers relationship conflict"
    ],
    currentFocus: ["Boundary-setting", "Self-compassion"]
  },
  expanded: {
    title: "AI-Generated Journey Summary",
    sections: [
      {
        title: "Clinical Progress",
        content: "Your depression score improved from 18 to 6 on the PHQ-9 scale, representing a 67% reduction over 10 sessions. Your anxiety improved from 15 to 5 on the GAD-7 scale, also a 67% reduction. This represents clinically significant improvement and moves you from moderate-severe to mild symptom range. The most dramatic improvement occurred between Sessions 7-9 when you consistently applied grounding techniques during work stress.",
        isCollapsed: false
      },
      {
        title: "Therapeutic Strategies Learned",
        content: "You've engaged deeply with three primary therapeutic techniques:\n\n- Laddering technique (Session 9): Helped identify core beliefs about self-worth stemming from childhood experiences. You were able to trace surface-level thoughts ('I'm not good enough at work') to deeper beliefs ('I'm fundamentally unlovable').\n\n- 4-7-8 breathing (Session 8): You reported using this 2x daily and noted a 40% reduction in acute anxiety episodes.\n\n- Grounding techniques (Session 7): Particularly effective during work presentations. You've used the 5-4-3-2-1 sensory technique before three major meetings with positive outcomes.\n\nYou've shown strong engagement with behavioral exercises and cognitive restructuring, completing 83% of homework assignments.",
        isCollapsed: false
      },
      {
        title: "Identified Patterns",
        content: "A clear pattern has emerged through our sessions: work stress triggers relationship conflict, which leads to negative self-talk and withdrawal. Specifically:\n\n1. High-pressure work deadlines increase irritability\n2. Irritability leads to snapping at partner/friends\n3. Conflict triggers shame and 'I'm a bad person' thoughts\n4. Shame leads to social withdrawal\n5. Isolation worsens depressive symptoms\n\nWhen you practice self-compassion at step 3 (recognizing stress rather than labeling yourself), you can interrupt this cycle effectively. Sessions 9 and 10 showed you successfully doing this.",
        isCollapsed: false
      },
      {
        title: "Current Treatment Focus",
        content: "Your therapist is currently helping you develop:\n\n- Boundary-setting skills: Learning to say 'no' to additional work commitments without guilt. Your homework from Session 10 focuses on practicing this with a specific friend.\n\n- Self-worth independent of achievement: Challenging the belief that your value comes only from productivity. The laddering work revealed this as a core schema.\n\n- Relationship communication: Expressing needs before reaching the point of irritability. You're practicing 'I feel' statements with your partner.",
        isCollapsed: false
      },
      {
        title: "Long-term Goals",
        content: "Continue building resilience through:\n\n1. Consistent homework completion (maintain 80%+ rate)\n2. Active participation in session exercises\n3. Generalizing coping skills to new situations\n4. Building a stronger support network\n5. Maintaining the gains you've made while pushing into new growth areas\n\nRecommended next steps include exploring the family-of-origin patterns identified in Session 9 and continuing to practice boundary-setting in increasingly challenging situations.",
        isCollapsed: false
      }
    ]
  }
};

/** AI Chat Widget Data */
export const aiChatData: AIChatData = {
  description: "Chat with Dobby to prepare for sessions, ask questions, and message your therapist.",
  expandedDescription: {
    title: "Meet Dobby - Your Therapy Companion",
    capabilities: [
      "Prepare for upcoming sessions",
      "Ask mental health questions",
      "Save topics to discuss later",
      "Message your therapist",
      "Reference your session data"
    ]
  },
  prompts: [
    {
      id: "prompt-1",
      text: "Why does my mood drop after stressful work days?",
      priority: 1,
      category: "pattern-exploration"
    },
    {
      id: "prompt-2",
      text: "Help me prep to discuss boundaries with my therapist",
      priority: 2,
      category: "session-prep"
    },
    {
      id: "prompt-3",
      text: "What patterns have you noticed in my sessions?",
      priority: 3,
      category: "pattern-exploration"
    },
    {
      id: "prompt-4",
      text: "Remind me about the laddering technique from last session",
      priority: 4,
      category: "homework"
    },
    {
      id: "prompt-5",
      text: "I want to message my therapist about something I forgot to mention",
      priority: 5,
      category: "therapist-communication"
    },
    {
      id: "prompt-6",
      text: "What should I focus on before my next appointment?",
      priority: 6,
      category: "session-prep"
    }
  ]
};

/** To-Do Widget Data */
export const toDoData: ToDoData = {
  active: [
    {
      id: "task-1",
      text: "Set boundary with friend about time commitments",
      completed: false,
      sourceSession: "Session 10 (Dec 17)",
      createdAt: "2024-12-17"
    },
    {
      id: "task-2",
      text: "Journal daily wins and moments of self-advocacy",
      completed: false,
      sourceSession: "Session 10 (Dec 17)",
      createdAt: "2024-12-17"
    },
    {
      id: "task-3",
      text: "Conduct behavioral experiment with trusted friend",
      completed: false,
      sourceSession: "Session 9 (Dec 10)",
      createdAt: "2024-12-10"
    }
  ],
  completed: [
    {
      id: "task-4",
      text: "Practice self-compassion when negative thoughts arise",
      completed: true,
      sourceSession: "Session 9 (Dec 10)",
      createdAt: "2024-12-10"
    },
    {
      id: "task-5",
      text: "Use 4-7-8 breathing when anxious 2x/day",
      completed: true,
      sourceSession: "Session 8 (Dec 3)",
      createdAt: "2024-12-03"
    },
    {
      id: "task-6",
      text: "Track anxiety triggers in journal for one week",
      completed: true,
      sourceSession: "Session 8 (Dec 3)",
      createdAt: "2024-12-03"
    }
  ]
};

/** Progress Patterns Widget Data */
export const progressPatternsData: ProgressPatternsData = {
  moodTrend: {
    data: [
      { session: 1, date: "2024-10-15", mood: 3 },
      { session: 2, date: "2024-10-22", mood: 4 },
      { session: 3, date: "2024-10-29", mood: 3 },
      { session: 4, date: "2024-11-05", mood: 4 },
      { session: 5, date: "2024-11-12", mood: 5 },
      { session: 6, date: "2024-11-19", mood: 4 },
      { session: 7, date: "2024-11-26", mood: 6 },
      { session: 8, date: "2024-12-03", mood: 6 },
      { session: 9, date: "2024-12-10", mood: 8 },
      { session: 10, date: "2024-12-17", mood: 8 }
    ],
    insight: "Your mood has improved 167% over the last 10 sessions, from an average of 3/10 to 8/10. The most significant jump occurred between Sessions 8-9 when you had your breakthrough about self-worth. Weeks with completed breathing exercises show consistently higher mood ratings.",
    improvement: 167
  },
  homeworkImpact: {
    data: [
      { week: "Week 1", startDate: "2024-10-15", endDate: "2024-10-21", completionRate: 50, averageMood: 3.5 },
      { week: "Week 2", startDate: "2024-10-22", endDate: "2024-10-28", completionRate: 60, averageMood: 4.0 },
      { week: "Week 3", startDate: "2024-10-29", endDate: "2024-11-04", completionRate: 40, averageMood: 3.5 },
      { week: "Week 4", startDate: "2024-11-05", endDate: "2024-11-11", completionRate: 70, averageMood: 4.5 },
      { week: "Week 5", startDate: "2024-11-12", endDate: "2024-11-18", completionRate: 80, averageMood: 5.0 },
      { week: "Week 6", startDate: "2024-11-19", endDate: "2024-11-25", completionRate: 60, averageMood: 4.5 },
      { week: "Week 7", startDate: "2024-11-26", endDate: "2024-12-02", completionRate: 90, averageMood: 6.5 },
      { week: "Week 8", startDate: "2024-12-03", endDate: "2024-12-09", completionRate: 100, averageMood: 7.0 },
      { week: "Week 9", startDate: "2024-12-10", endDate: "2024-12-16", completionRate: 85, averageMood: 8.0 },
      { week: "Week 10", startDate: "2024-12-17", endDate: "2024-12-23", completionRate: 80, averageMood: 8.0 }
    ],
    insight: "Weeks with 80%+ homework completion show 35% better mood scores on average. Your highest completion rate was Week 8 (100%) when you fully committed to the breathing exercises, correlating with a significant mood boost. The data suggests that consistent practice, even when motivation is low, directly impacts your wellbeing.",
    correlation: "Strong positive (r=0.82)"
  },
  sessionConsistency: {
    data: generateConsistencyCalendar(),
    insight: "You've maintained consistent weekly sessions with an average of 7.2 days between appointments. You missed no sessions during this period, demonstrating strong commitment to your therapeutic journey. The consistency has contributed to building momentum in your progress.",
    averageDaysBetween: 7.2
  },
  strategyEffectiveness: {
    data: [
      {
        strategy: "Grounding (5-4-3-2-1)",
        timesUsed: 23,
        moodCorrelation: 0.85,
        description: "Used before work presentations and during anxiety spikes. High success rate in reducing acute symptoms."
      },
      {
        strategy: "4-7-8 Breathing",
        timesUsed: 42,
        moodCorrelation: 0.78,
        description: "Daily practice twice per day. Most effective when used proactively rather than reactively."
      },
      {
        strategy: "Laddering Technique",
        timesUsed: 8,
        moodCorrelation: 0.72,
        description: "Used in sessions to identify core beliefs. Led to major breakthrough in Session 9."
      },
      {
        strategy: "Self-Compassion Phrases",
        timesUsed: 18,
        moodCorrelation: 0.68,
        description: "Replacing self-critical thoughts with compassionate responses. Still developing consistency."
      }
    ],
    insight: "Grounding techniques show the highest correlation with mood improvement (+0.85). The 4-7-8 breathing, while used most frequently (42 times), shows slightly lower correlation, suggesting quality of practice matters as much as quantity. Laddering, though used less often, produced the most profound shifts in understanding.",
    topStrategy: "Grounding (5-4-3-2-1)"
  }
};

/** Helper function to generate calendar data for session consistency */
function generateConsistencyCalendar(): SessionConsistencyDay[] {
  const sessionDates = [
    "2024-10-15", "2024-10-22", "2024-10-29", "2024-11-05", "2024-11-12",
    "2024-11-19", "2024-11-26", "2024-12-03", "2024-12-10", "2024-12-17"
  ];

  const calendar: SessionConsistencyDay[] = [];
  const startDate = new Date("2024-10-01");
  const endDate = new Date("2024-12-31");

  for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
    const dateStr = d.toISOString().split("T")[0];
    calendar.push({
      date: dateStr,
      hasSession: sessionDates.includes(dateStr),
      dayOfWeek: d.getDay()
    });
  }

  return calendar;
}

/** Therapist Bridge Widget Data */
export const therapistBridgeData: TherapistBridgeData = {
  compact: {
    conversationStarters: {
      id: "starter-compact",
      text: "Family boundaries"
    },
    shareProgress: {
      id: "progress-compact",
      text: "Completed 3-week sleep plan"
    },
    sessionPrep: {
      id: "prep-compact",
      text: "Review anxiety journal"
    }
  },
  expanded: {
    conversationStarters: {
      title: "Conversation Starters",
      items: [
        {
          id: "starter-1",
          text: "How work stress connects to relationship patterns",
          context: "You've mentioned this 3 times but haven't explored it deeply"
        },
        {
          id: "starter-2",
          text: "Family boundary-setting experiences",
          context: "You completed homework around this and might benefit from discussing your experience"
        },
        {
          id: "starter-3",
          text: "Self-worth patterns from past relationships",
          context: "Session 9 breakthrough could be expanded further"
        }
      ]
    },
    shareProgress: {
      title: "Share Progress with Therapist",
      items: [
        {
          id: "progress-1",
          text: "3-week sleep hygiene completion streak",
          context: "Consistent bedtime, no screens before bed"
        },
        {
          id: "progress-2",
          text: "40% anxiety score reduction this week",
          context: "From 10 to 6 on GAD-7 scale"
        },
        {
          id: "progress-3",
          text: "Successfully set boundary with friend about time commitments",
          context: "First time doing this without excessive guilt"
        }
      ]
    },
    sessionPrep: {
      title: "Session Prep",
      items: [
        {
          id: "prep-1",
          text: "Review anxiety trigger journal entries from this week",
          context: "Identify patterns to discuss"
        },
        {
          id: "prep-2",
          text: "Prepare questions about grounding technique application in work settings",
          context: "You mentioned wanting to use it in meetings"
        },
        {
          id: "prep-3",
          text: "Bring up incomplete behavioral experiment",
          context: "Discuss what held you back from completing it"
        }
      ]
    },
    nextSessionDate: "December 20, 2024"
  }
};

/** Sessions Data - 10 sessions from Dec 17 to Oct 15 */
export const sessionsData: Session[] = [
  {
    id: "session-10",
    sessionNumber: 10,
    date: "2024-12-17",
    displayDate: "Dec 17",
    duration: 50,
    mood: "positive",
    moodEmoji: "happy",
    topics: ["Boundary-setting", "Self-advocacy", "Progress review"],
    strategy: "Behavioral activation",
    strategyDescription: "Setting small achievable goals to build confidence",
    actions: [
      { id: "action-10-1", text: "Set boundary with friend" },
      { id: "action-10-2", text: "Journal daily wins" }
    ],
    isMilestone: true,
    milestoneText: "Maintained gains",
    transcript: `Therapist: Welcome back! How has your week been since our last session?

Patient: It's been really good actually. I noticed I was feeling anxious about a friend asking for a favor, and instead of just saying yes like I always do, I actually paused and thought about whether I had the capacity.

Therapist: That's wonderful! Tell me more about that moment. What was going through your mind?

Patient: Well, I remembered what we talked about last time - that saying no doesn't make me a bad person. So I told them I couldn't help this week but could next week. And they were totally fine with it!

Therapist: How did it feel after?

Patient: Honestly? A bit anxious at first. That old guilt tried to creep in. But then I used the self-compassion phrase we practiced - "I'm allowed to have limits" - and the anxiety passed pretty quickly.

Therapist: I'm so proud of the progress you're making. Let's talk about how we can build on this success...

Patient: I'd really like to work on being more consistent with this. Sometimes I still slip into people-pleasing mode without even realizing it.

Therapist: That's completely normal. Change isn't linear. What matters is that you're catching yourself more often. Let's create some homework around this...`,
    summary: "Excellent session reviewing progress on boundary-setting. Patient successfully implemented boundaries with friend and used self-compassion techniques effectively. Discussed maintaining gains and extending boundary practice to more challenging situations."
  },
  {
    id: "session-9",
    sessionNumber: 9,
    date: "2024-12-10",
    displayDate: "Dec 10",
    duration: 45,
    mood: "positive",
    moodEmoji: "happy",
    topics: ["Self-worth", "Past relationships", "Core beliefs"],
    strategy: "Laddering technique",
    strategyDescription: "Tracing surface thoughts to deeper core beliefs about self",
    actions: [
      { id: "action-9-1", text: "Self-compassion practice" },
      { id: "action-9-2", text: "Behavioral experiment" }
    ],
    isMilestone: true,
    milestoneText: "Breakthrough: Self-compassion",
    transcript: `Therapist: Last week you mentioned feeling like you weren't enough at work. I'd like to explore that more deeply today using something called laddering. Are you open to that?

Patient: Sure, though I'm not sure what that means.

Therapist: It's a way of tracing a surface-level thought to its deeper roots. So when you think "I'm not enough at work" - what's the worst part about that for you?

Patient: I guess... that people will see I'm a fraud. That I don't deserve my position.

Therapist: And if people saw that - what would that mean about you?

Patient: That I've been fooling everyone. That I'm not actually capable of anything.

Therapist: And if you weren't capable... what does that say about you as a person?

Patient: [long pause] That I'm... unlovable. That the only reason people stick around is because they think I'm competent. If they knew the real me, they'd leave.

Therapist: [gently] That's a really important realization. This belief - "I'm unlovable unless I'm achieving" - do you recognize where that might come from?

Patient: [tearfully] My dad. He only paid attention to me when I brought home good grades. Otherwise, I was invisible.

Therapist: You're doing incredible work right now. What you just uncovered is a core belief that's been driving so much of your anxiety and people-pleasing...`,
    summary: "Major breakthrough session using laddering technique. Patient traced work anxiety to core belief about being unlovable without achievement, connected to childhood experiences with father. Deeply emotional session with significant insight gained."
  },
  {
    id: "session-8",
    sessionNumber: 8,
    date: "2024-12-03",
    displayDate: "Dec 3",
    duration: 48,
    mood: "neutral",
    moodEmoji: "neutral",
    topics: ["Anxiety management", "Breathing techniques", "Sleep hygiene"],
    strategy: "4-7-8 Breathing",
    strategyDescription: "Structured breathing to activate parasympathetic nervous system",
    actions: [
      { id: "action-8-1", text: "Practice 4-7-8 breathing 2x/day" },
      { id: "action-8-2", text: "Track anxiety triggers" }
    ],
    isMilestone: false,
    transcript: `Therapist: How has your anxiety been this week?

Patient: Pretty rough, honestly. I had two big presentations at work and I could feel the panic building both times.

Therapist: Let's work on something you can use in those moments. Have you heard of 4-7-8 breathing?

Patient: No, what is it?

Therapist: It's a specific breathing pattern - breathe in for 4 counts, hold for 7, exhale for 8. The long exhale activates your body's calming response. Want to try it now?

Patient: Okay.

[They practice the technique together multiple times]

Therapist: How do you feel now compared to when we started?

Patient: Actually... calmer. My shoulders dropped. I didn't even realize how tense I was.

Therapist: This works because you're directly telling your nervous system to calm down. I'd like you to practice this twice a day, every day - not just when anxious. Building the habit makes it more automatic when you really need it.

Patient: That makes sense. Morning and before bed?

Therapist: Perfect. Let's also talk about your sleep, since that often connects to daytime anxiety...`,
    summary: "Focused session on anxiety management. Introduced and practiced 4-7-8 breathing technique with immediate positive response. Connected poor sleep hygiene to anxiety levels. Assigned daily breathing practice and anxiety trigger tracking."
  },
  {
    id: "session-7",
    sessionNumber: 7,
    date: "2024-11-26",
    displayDate: "Nov 26",
    duration: 45,
    mood: "neutral",
    moodEmoji: "neutral",
    topics: ["Family dynamics", "Holiday stress", "Grounding"],
    strategy: "Grounding (5-4-3-2-1)",
    strategyDescription: "Using five senses to anchor to present moment during distress",
    actions: [
      { id: "action-7-1", text: "Use grounding before family dinner" },
      { id: "action-7-2", text: "Notice body tension signals" }
    ],
    isMilestone: true,
    milestoneText: "New strategy learned",
    transcript: `Therapist: With Thanksgiving this week, I wanted to check in about how you're feeling about family time.

Patient: Honestly, dreading it. My mom always makes comments about my job, my relationships, everything. By the end of dinner I'm always a wreck.

Therapist: What happens in your body when she makes those comments?

Patient: My chest gets tight, I can feel my face getting hot. Sometimes I literally zone out - like I'm watching from outside my body.

Therapist: That zoning out is dissociation - your nervous system's way of protecting you when things feel like too much. I want to teach you a grounding technique that can help you stay present instead of disconnecting.

Patient: Okay, that sounds helpful.

Therapist: It's called 5-4-3-2-1. When you feel that dissociation starting, you name 5 things you can see, 4 you can touch, 3 you can hear, 2 you can smell, and 1 you can taste. It anchors you to the present moment.

[They practice together]

Patient: That's interesting - I immediately felt more in my body when I started noticing things around me.

Therapist: Exactly. You might practice this before you even walk into dinner, as a preventive measure. Being grounded before stress hits makes you more resilient to it...`,
    summary: "Pre-holiday session focused on managing family stress. Introduced 5-4-3-2-1 grounding technique to address patient's dissociation patterns. Connected physical symptoms to emotional triggers. Assigned preventive grounding practice before family gathering."
  },
  {
    id: "session-6",
    sessionNumber: 6,
    date: "2024-11-19",
    displayDate: "Nov 19",
    duration: 50,
    mood: "low",
    moodEmoji: "sad",
    topics: ["Loneliness", "Social withdrawal", "Support network"],
    strategy: "Behavioral activation",
    strategyDescription: "Small steps to re-engage with pleasurable activities",
    actions: [
      { id: "action-6-1", text: "Text one friend this week" },
      { id: "action-6-2", text: "Leave house once for non-essential task" }
    ],
    isMilestone: false,
    transcript: `Therapist: You seem quieter today. What's been going on?

Patient: I've been isolating a lot. Haven't seen friends in two weeks. When people text me I just... don't respond. And then I feel guilty about that too.

Therapist: Tell me what the isolation feels like from the inside.

Patient: It feels safe at first. Like I don't have to pretend to be okay. But after a few days it just feels empty. And then I start thinking everyone probably forgot about me anyway.

Therapist: That's a pattern we've seen before - the isolation starts as protection but becomes its own problem. What's one small thing you could do this week to reconnect?

Patient: I guess I could text my friend Sarah. She's been really understanding.

Therapist: That sounds like a good start. What might you say?

Patient: Maybe just... "Hey, sorry I've been MIA. Rough couple of weeks. Want to grab coffee sometime?"

Therapist: Perfect. Honest and simple. How does it feel to think about sending that?

Patient: Scary. But also... maybe okay? I know she won't judge me.

Therapist: I'd also like you to leave the house once this week for something that isn't required. A walk, coffee shop, anything. Just to break the pattern of staying in...`,
    summary: "Patient struggling with social withdrawal and isolation. Discussed how protective isolation becomes harmful over time. Assigned small behavioral activation tasks: text one friend, leave house once for non-essential activity."
  },
  {
    id: "session-5",
    sessionNumber: 5,
    date: "2024-11-12",
    displayDate: "Nov 12",
    duration: 45,
    mood: "neutral",
    moodEmoji: "neutral",
    topics: ["Sleep issues", "Rumination", "Thought patterns"],
    strategy: "Worry time scheduling",
    strategyDescription: "Designating specific time for worries to reduce rumination",
    actions: [
      { id: "action-5-1", text: "Set 15-min worry time daily" },
      { id: "action-5-2", text: "Write down nighttime worries" }
    ],
    isMilestone: true,
    milestoneText: "PHQ-9 improved",
    transcript: `Therapist: Your PHQ-9 score improved from 12 to 9 this week. How are you feeling about that?

Patient: Honestly surprised. I haven't been sleeping well at all, so I thought it would be worse.

Therapist: Tell me about the sleep issues.

Patient: I lie in bed and my brain just won't turn off. I replay everything from the day, everything I need to do tomorrow, things I said wrong from five years ago...

Therapist: That sounds exhausting. The technical term is rumination - your mind getting stuck in loops. There's a paradoxical technique that might help: scheduled worry time.

Patient: You want me to schedule time to worry?

Therapist: Exactly. When you try to suppress worries, they push back harder. But if you tell your brain "I'll deal with this at 6pm tomorrow," it often lets go for now.

Patient: That's... kind of weird but makes sense.

Therapist: Let's try it this week. Set 15 minutes at the same time each day. Write down any worries that come up outside that time, and save them for your designated worry period. Often by the time you get there, the worry has lost its urgency...`,
    summary: "PHQ-9 improved to 9 (from 12). Addressed sleep difficulties caused by rumination patterns. Introduced scheduled worry time technique. Assigned daily 15-minute worry period and worry journal for nighttime thoughts."
  },
  {
    id: "session-4",
    sessionNumber: 4,
    date: "2024-11-05",
    displayDate: "Nov 5",
    duration: 50,
    mood: "low",
    moodEmoji: "sad",
    topics: ["Work stress", "Perfectionism", "Self-criticism"],
    strategy: "Cognitive restructuring",
    strategyDescription: "Identifying and challenging negative thought patterns",
    actions: [
      { id: "action-4-1", text: "Catch 3 self-critical thoughts daily" },
      { id: "action-4-2", text: "Ask 'What would I tell a friend?'" }
    ],
    isMilestone: false,
    transcript: `Therapist: How was work this week?

Patient: Terrible. I made a mistake in a report - a small one, but I spent the entire week beating myself up about it. I kept thinking everyone must think I'm incompetent.

Therapist: Walk me through what happened and what you told yourself.

Patient: The numbers in one section were wrong. My boss caught it before it went to the client. He wasn't even upset - just asked me to fix it. But in my head I was like "You're so stupid. You shouldn't even have this job. Everyone knows you don't belong here."

Therapist: That's a lot of harsh criticism for a small, fixable mistake. What would you say if a friend came to you with the same situation?

Patient: I'd probably say mistakes happen, fix it and move on, it's not a big deal.

Therapist: Why is it so hard to give yourself that same kindness?

Patient: [pause] I don't know. It feels like if I'm not hard on myself, I won't improve. Like self-criticism is what keeps me performing.

Therapist: That's a common belief, but research shows self-criticism actually impairs performance. Self-compassion leads to more resilience, more risk-taking, more growth. This week, I'd like you to catch those self-critical thoughts and practice asking "What would I tell a friend?"...`,
    summary: "Patient struggling with self-criticism after minor work mistake. Explored perfectionism patterns and fear of being 'found out' (imposter syndrome). Introduced self-compassion reframe technique. Assigned thought-catching exercise."
  },
  {
    id: "session-3",
    sessionNumber: 3,
    date: "2024-10-29",
    displayDate: "Oct 29",
    duration: 45,
    mood: "low",
    moodEmoji: "sad",
    topics: ["Relationship conflict", "Communication", "Anger"],
    strategy: "I-statements",
    strategyDescription: "Expressing needs without blame using 'I feel' format",
    actions: [
      { id: "action-3-1", text: "Practice I-statements with partner" },
      { id: "action-3-2", text: "Notice anger body signals" }
    ],
    isMilestone: false,
    transcript: `Therapist: You mentioned on the phone that you had a conflict with your partner. Can you tell me more?

Patient: We had this huge fight about something stupid - who forgot to take out the trash. But it escalated into yelling and bringing up stuff from months ago.

Therapist: What happened in your body as the fight escalated?

Patient: I could feel myself getting hot, my heart racing. And then I just... snapped. Said things I didn't mean.

Therapist: It sounds like you went from 0 to 100 very quickly. Let's slow that down and see what happened in between.

Patient: I guess... I was already stressed from work. And when they mentioned the trash, it felt like criticism. Like I can't do anything right.

Therapist: So the trash comment triggered an old story - "I can't do anything right." And that story probably felt true in that moment.

Patient: Yeah. Even though logically I know it's not.

Therapist: Let's work on a different way to express what you're feeling in those moments. Have you heard of I-statements?...`,
    summary: "Explored recent relationship conflict and identified pattern of work stress triggering relationship reactivity. Connected conflict to underlying 'not good enough' narrative. Introduced I-statements for healthier communication."
  },
  {
    id: "session-2",
    sessionNumber: 2,
    date: "2024-10-22",
    displayDate: "Oct 22",
    duration: 45,
    mood: "low",
    moodEmoji: "sad",
    topics: ["History intake", "Childhood", "Family patterns"],
    strategy: "Active listening",
    strategyDescription: "Building therapeutic alliance through deep listening",
    actions: [
      { id: "action-2-1", text: "Write about earliest anxiety memory" },
      { id: "action-2-2", text: "Notice family patterns in current life" }
    ],
    isMilestone: true,
    milestoneText: "Baseline established",
    transcript: `Therapist: Today I'd like to understand more about your history. Can you tell me about your childhood?

Patient: It was... complicated. My parents divorced when I was 8. My dad moved across the country and I didn't see him much after that.

Therapist: How did that affect you?

Patient: I think I always felt like it was somehow my fault. Like if I'd been a better kid, he would have stayed.

Therapist: That's a heavy belief for a child to carry. Do you still carry that belief?

Patient: Sometimes. When relationships end, I always assume I did something wrong. Even at work - if someone's upset, I think it must be because of me.

Therapist: So you learned early that you were responsible for other people's feelings and choices.

Patient: Yeah, I guess so. My mom relied on me a lot after the divorce. I became the emotional support, even though I was just a kid.

Therapist: That's called parentification - when a child takes on adult emotional responsibilities too young. It often leads to patterns like people-pleasing and difficulty knowing your own needs...`,
    summary: "Detailed history intake session. Explored childhood experiences including parental divorce, father absence, and early parentification. Established baseline understanding of core patterns: people-pleasing, over-responsibility, difficulty identifying own needs."
  },
  {
    id: "session-1",
    sessionNumber: 1,
    date: "2024-10-15",
    displayDate: "Oct 15",
    duration: 60,
    mood: "low",
    moodEmoji: "sad",
    topics: ["Intake", "Presenting concerns", "Treatment goals"],
    strategy: "Assessment",
    strategyDescription: "Initial evaluation and goal-setting",
    actions: [
      { id: "action-1-1", text: "Complete PHQ-9 and GAD-7" },
      { id: "action-1-2", text: "Journal about what brings you to therapy" }
    ],
    isMilestone: true,
    milestoneText: "Therapy journey begins",
    transcript: `Therapist: Welcome. I'm glad you decided to reach out. Can you tell me what brings you to therapy today?

Patient: I've been struggling for a while now. Maybe years. I just feel... stuck. Like nothing I do is ever good enough. And I'm so anxious all the time - about work, about relationships, about everything.

Therapist: That sounds really hard. Can you tell me more about what "stuck" feels like?

Patient: Like I'm going through the motions. I wake up, go to work, come home, sleep. But I don't feel alive. Just... empty. And tired. So tired.

Therapist: When did you first notice feeling this way?

Patient: Probably after my last relationship ended, about a year ago. But honestly, looking back, I think I've always been anxious. I just used to be better at hiding it.

Therapist: It takes courage to recognize you need support and to reach out. What are you hoping to get from our work together?

Patient: I want to feel like myself again. Or maybe discover who I actually am when I'm not just trying to please everyone else. And I want to stop feeling so anxious all the time.

Therapist: Those are wonderful goals. Let's start by understanding more about what's been happening...`,
    summary: "Initial intake session. Patient presents with depression, anxiety, and people-pleasing patterns following relationship breakup. Completed baseline assessments (PHQ-9: 18, GAD-7: 15). Goals established: reduce anxiety, develop authentic self, address people-pleasing."
  }
];

/** Timeline Data - Derived from sessions */
export const timelineData: TimelineEntry[] = sessionsData.map((session) => ({
  id: `timeline-${session.id}`,
  sessionId: session.id,
  date: session.date,
  displayDate: session.displayDate,
  topicPreview: session.topics[0].split(" ")[0], // First word of first topic
  mood: session.mood,
  moodColor: session.mood === "positive" ? "#A8C69F" : session.mood === "neutral" ? "#B8A5D6" : "#F4A69D",
  isMilestone: session.isMilestone,
  milestoneText: session.milestoneText
}));

/** Mood color mapping utility */
export const getMoodColor = (mood: SessionMood): string => {
  switch (mood) {
    case "positive":
      return "#A8C69F"; // Soft Green
    case "neutral":
      return "#B8A5D6"; // Lavender
    case "low":
      return "#F4A69D"; // Gentle Rose
    default:
      return "#B8A5D6";
  }
};

/** Mood emoji mapping utility */
export const getMoodEmoji = (mood: SessionMood): string => {
  switch (mood) {
    case "positive":
      return "happy";
    case "neutral":
      return "neutral";
    case "low":
      return "sad";
    default:
      return "neutral";
  }
};

/** Mood border class mapping utility */
export const getMoodBorderClass = (mood: SessionMood): string => {
  switch (mood) {
    case "positive":
      return "border-l-green-200";
    case "neutral":
      return "border-l-blue-200";
    case "low":
      return "border-l-rose-200";
    default:
      return "border-l-blue-200";
  }
};

/** Complete dashboard data export */
export const dashboardV2Data: DashboardV2Data = {
  notesGoals: notesGoalsData,
  aiChat: aiChatData,
  toDo: toDoData,
  progressPatterns: progressPatternsData,
  therapistBridge: therapistBridgeData,
  sessions: sessionsData,
  timeline: timelineData
};

/** Default export */
export default dashboardV2Data;
