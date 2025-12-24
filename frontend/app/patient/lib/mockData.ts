/**
 * Mock data for TherapyBridge Dashboard demo
 * - 10 therapy sessions with realistic content
 * - Tasks, milestones, and progress metrics
 * - Timeline and chat conversation data
 */

import {
  Session,
  Task,
  ProgressMetric,
  ChatMessage,
  TimelineEntry,
  MajorEventEntry,
  SessionTimelineEvent,
  TimelineEvent
} from './types';

export const sessions: Session[] = [
  {
    id: 's10',
    date: 'May 9',
    rawDate: new Date('2025-05-09'),
    duration: '50m',
    therapist: 'Dr. Sarah Chen',
    mood: 'positive',
    topics: ['Boundaries', 'Family dynamics'],
    strategy: 'Assertiveness training',
    actions: ['Set clear boundaries', 'Practice saying no'],
    transcript: [
      { speaker: 'Therapist', text: 'How did the boundary-setting go this week?', timestamp: '01:23' },
      { speaker: 'Patient', text: "It was tough but I actually said no to my mom's request to babysit on my work day.", timestamp: '01:45' },
      { speaker: 'Therapist', text: 'That\'s a significant step. How did it feel?', timestamp: '03:12' },
      { speaker: 'Patient', text: 'Scary at first, but then relieving. Like a weight lifted.', timestamp: '04:08' }
    ],
    patientSummary: 'Made breakthrough progress on setting boundaries with family. Successfully practiced assertiveness techniques learned in previous sessions.'
  },
  {
    id: 's9',
    date: 'May 2',
    rawDate: new Date('2025-05-02'),
    duration: '45m',
    therapist: 'Dr. Sarah Chen',
    mood: 'positive',
    topics: ['Self-worth', 'Past relationships'],
    strategy: 'Laddering technique',
    actions: ['Self-compassion practice', 'Behavioral experiment'],
    milestone: {
      title: 'Breakthrough: Self-compassion',
      description: 'Patient achieved major insight connecting childhood experiences to current self-worth patterns'
    },
    transcript: [
      { speaker: 'Therapist', text: 'Tell me about the compassion exercise you tried.', timestamp: '02:15' },
      { speaker: 'Patient', text: 'I wrote that letter to my younger self. I cried for an hour but it helped me realize I was never the problem.', timestamp: '02:42' },
      { speaker: 'Therapist', text: 'That\'s a profound realization. How does that shift how you see yourself now?', timestamp: '05:18' },
      { speaker: 'Patient', text: 'I think... I think I deserve kindness. Even from myself.', timestamp: '07:33' }
    ],
    patientSummary: 'Breakthrough session with emotional release. Patient connected childhood neglect to adult self-worth issues and demonstrated genuine self-compassion.',
    deep_analysis: {
      progress_indicators: {
        symptom_reduction: {
          detected: true,
          description: 'Significant reduction in negative self-talk and self-blame patterns. Patient demonstrates internalized understanding that childhood neglect was not their fault.',
          confidence: 0.92
        },
        skill_development: [
          {
            skill: 'Self-compassion practice',
            proficiency: 'developing',
            evidence: 'Successfully completed compassionate letter-writing exercise with emotional breakthrough'
          },
          {
            skill: 'Emotional awareness and acceptance',
            proficiency: 'proficient',
            evidence: 'Allowed emotional release without judgment, recognized crying as healing rather than weakness'
          }
        ],
        goal_progress: [
          {
            goal: 'Develop healthier self-image',
            status: 'on_track',
            evidence: 'Verbalized deserving kindness from self - major shift from previous negative core beliefs'
          }
        ],
        behavioral_changes: [
          'Engaging with difficult emotions rather than suppressing them',
          'Practicing self-directed compassion exercises independently',
          'Reframing childhood experiences through adult understanding'
        ]
      },
      therapeutic_insights: {
        key_realizations: [
          'Connected childhood neglect to current self-worth struggles - "I was never the problem"',
          'Recognized deserving of self-kindness as fundamental truth, not something to earn',
          'Understanding that emotional release (crying) is part of healing, not weakness'
        ],
        patterns: [
          'Historical pattern of internalizing others\' failures as personal deficiencies',
          'Tendency to intellectualize emotions to avoid feeling them fully',
          'Gradual shift from external validation-seeking to internal self-acceptance'
        ],
        growth_areas: [
          'Continuing to practice self-compassion in daily moments, not just exercises',
          'Extending kindness to present-day self, not only inner child',
          'Challenging remaining perfectionistic standards in work and relationships'
        ],
        strengths: [
          'Willingness to engage with painful material and vulnerability',
          'Capacity for deep emotional insight and self-reflection',
          'Ability to connect past experiences to present patterns',
          'Resilience in facing difficult emotions head-on'
        ]
      },
      coping_skills: {
        learned: ['Compassionate letter-writing', 'Inner child dialogue', 'Emotional acceptance', 'Self-validation'],
        proficiency: {
          'Compassionate_letter_writing': 'developing',
          'Inner_child_dialogue': 'developing',
          'Emotional_acceptance': 'proficient',
          'Self_validation': 'beginner'
        },
        practice_recommendations: [
          'Continue daily self-compassion check-ins using the 3-question format (What am I feeling? What do I need? How can I give that to myself?)',
          'Practice compassionate self-talk when perfectionism triggers arise at work',
          'Use the letter-writing technique when experiencing shame or self-blame'
        ]
      },
      therapeutic_relationship: {
        engagement_level: 'high',
        engagement_evidence: 'Deeply engaged with therapeutic process, willing to try challenging exercises, brought completed homework with genuine effort',
        openness: 'very_open',
        openness_evidence: 'Shared profound emotional vulnerability, allowed tears and emotional expression in session, connected openly about childhood trauma',
        alliance_strength: 'strong',
        alliance_evidence: 'High trust evident in willingness to explore painful material, follows through on therapeutic assignments, collaborative in session'
      },
      recommendations: {
        practices: [
          'Daily self-compassion meditation (5 minutes in morning)',
          'Continue letter-writing to younger self weekly',
          'Practice self-validation before seeking external reassurance',
          'Notice and note moments of self-kindness in journal'
        ],
        resources: [
          '"Self-Compassion" by Kristin Neff (especially Chapters 3-4 on shame and self-kindness)',
          'Loving-Kindness meditation app (start with self-directed practice)',
          'Adult Children of Emotionally Immature Parents support group (meets Thursdays)'
        ],
        reflection_prompts: [
          'What would you say to a friend experiencing what you\'re going through?',
          'How has childhood neglect shaped your current relationships?',
          'What does "deserving kindness" mean to you now versus before this session?',
          'When do you find it hardest to be compassionate toward yourself?'
        ]
      },
      confidence_score: 0.91,
      analyzed_at: '2024-12-10T15:45:00Z'
    },
    analysis_confidence: 0.91
  },
  {
    id: 's8',
    date: 'Apr 18',
    rawDate: new Date('2025-04-18'),
    duration: '48m',
    therapist: 'Dr. Sarah Chen',
    mood: 'neutral',
    topics: ['Work stress', 'Perfectionism'],
    strategy: 'Cognitive restructuring',
    actions: ['Challenge catastrophizing', 'Priority matrix exercise'],
    transcript: [
      { speaker: 'Therapist', text: 'What happened with the project deadline?', timestamp: '01:23' },
      { speaker: 'Patient', text: 'I stayed late every night but still felt like it wasn\'t good enough.', timestamp: '01:45' },
      { speaker: 'Therapist', text: 'Let\'s examine that thought - what\'s the evidence it wasn\'t good enough?', timestamp: '02:10' },
      { speaker: 'Patient', text: 'Well... my boss said it was excellent. But I saw all the flaws.', timestamp: '02:35' }
    ],
    patientSummary: 'Identified perfectionism pattern at work. Began recognizing cognitive distortions around performance standards.'
  },
  {
    id: 's7',
    date: 'Apr 4',
    rawDate: new Date('2025-04-04'),
    duration: '45m',
    therapist: 'Dr. Sarah Chen',
    mood: 'neutral',
    topics: ['Sleep issues', 'Anxiety'],
    strategy: 'Sleep hygiene protocol',
    actions: ['Create bedtime routine', 'Limit screen time'],
    milestone: {
      title: 'Completed 3-week sleep plan',
      description: 'Successfully implemented and maintained sleep hygiene improvements'
    },
    patientSummary: 'Completed three-week sleep improvement plan. Reporting better rest quality and reduced morning anxiety.'
  },
  {
    id: 's6',
    date: 'Mar 14',
    rawDate: new Date('2025-03-14'),
    duration: '50m',
    therapist: 'Dr. Sarah Chen',
    mood: 'low',
    topics: ['Depression episode', 'Isolation'],
    strategy: 'Behavioral activation',
    actions: ['Daily walk commitment', 'Social contact plan'],
    transcript: [
      { speaker: 'Therapist', text: 'How has your mood been this week?', timestamp: '01:15' },
      { speaker: 'Patient', text: 'Really low. I cancelled everything and stayed in bed most of Saturday.', timestamp: '01:30' },
      { speaker: 'Therapist', text: 'I appreciate you sharing that. What\'s one small thing you could do today?', timestamp: '02:05' },
      { speaker: 'Patient', text: 'Maybe... maybe just walk to the mailbox.', timestamp: '02:40' }
    ],
    patientSummary: 'Experiencing depressive episode. Developed behavioral activation plan starting with minimal achievable goals.'
  },
  {
    id: 's5',
    date: 'Feb 28',
    rawDate: new Date('2025-02-28'),
    duration: '45m',
    therapist: 'Dr. Sarah Chen',
    mood: 'neutral',
    topics: ['Relationship conflict', 'Communication'],
    strategy: 'Active listening skills',
    actions: ['Practice I-statements', 'Emotion labeling'],
    milestone: {
      title: 'First conflict resolution success',
      description: 'Successfully navigated difficult conversation with partner using therapeutic techniques'
    },
    patientSummary: 'Applied communication strategies with partner. First successful conflict resolution without escalation.'
  },
  {
    id: 's4',
    date: 'Feb 14',
    rawDate: new Date('2025-02-14'),
    duration: '50m',
    therapist: 'Dr. Sarah Chen',
    mood: 'low',
    topics: ['Childhood trauma', 'Trust issues'],
    strategy: 'Trauma-focused CBT',
    actions: ['Grounding techniques', 'Safety plan review'],
    transcript: [
      { speaker: 'Therapist', text: 'You mentioned feeling triggered this week. Can you tell me more?', timestamp: '01:20' },
      { speaker: 'Patient', text: 'My partner raised his voice and I just... froze. Like I was a kid again.', timestamp: '01:50' },
      { speaker: 'Therapist', text: 'Thank you for trusting me with that. Let\'s practice the grounding technique we discussed.', timestamp: '03:25' }
    ],
    patientSummary: 'Processing childhood trauma memories. Experiencing flashback triggers. Reinforced grounding and safety strategies.'
  },
  {
    id: 's3',
    date: 'Jan 31',
    rawDate: new Date('2025-01-31'),
    duration: '45m',
    therapist: 'Dr. Sarah Chen',
    mood: 'low',
    topics: ['Panic attacks', 'Health anxiety'],
    strategy: 'Interoceptive exposure',
    actions: ['Body scan meditation', 'Anxiety journal'],
    patientSummary: 'Continued panic management training. Patient practicing daily body awareness exercises.'
  },
  {
    id: 's2',
    date: 'Jan 17',
    rawDate: new Date('2025-01-17'),
    duration: '50m',
    therapist: 'Dr. Sarah Chen',
    mood: 'neutral',
    topics: ['Coping strategies', 'Emotional regulation'],
    strategy: 'DBT skills training',
    actions: ['TIPP technique', 'Distress tolerance'],
    milestone: {
      title: 'Mastered first coping skill',
      description: 'Successfully used TIPP technique during panic episode'
    },
    patientSummary: 'Learned and successfully applied TIPP technique independently. Building confidence in crisis management skills.'
  },
  {
    id: 's1',
    date: 'Jan 10',
    rawDate: new Date('2025-01-10'),
    duration: '50m',
    therapist: 'Dr. Sarah Chen',
    mood: 'neutral',
    topics: ['Initial assessment', 'Goal setting'],
    strategy: 'Intake & rapport building',
    actions: ['Complete PHQ-9', 'Set treatment goals'],
    milestone: {
      title: 'Treatment plan established',
      description: 'Collaboratively developed comprehensive treatment plan with measurable goals'
    },
    patientSummary: 'Initial intake session. Established therapeutic alliance and identified primary treatment goals: depression management, anxiety reduction, boundary development.'
  }
];

export const tasks: Task[] = [
  { id: 't1', text: 'Practice saying no to one request', completed: true, sessionId: 's10', sessionDate: 'May 9' },
  { id: 't2', text: 'Write compassion letter to younger self', completed: true, sessionId: 's9', sessionDate: 'May 2' },
  { id: 't3', text: 'Daily 10-minute walk', completed: true, sessionId: 's6', sessionDate: 'Mar 14' },
  { id: 't4', text: 'Challenge one catastrophic thought per day', completed: false, sessionId: 's8', sessionDate: 'Apr 18' },
  { id: 't5', text: 'Maintain sleep schedule (10pm bedtime)', completed: false, sessionId: 's7', sessionDate: 'Apr 4' },
  { id: 't6', text: 'Practice I-statements with partner', completed: false, sessionId: 's5', sessionDate: 'Feb 28' },
  { id: 't7', text: 'Grounding exercise when triggered', completed: true, sessionId: 's4', sessionDate: 'Feb 14' },
  { id: 't8', text: 'Keep anxiety journal', completed: false, sessionId: 's3', sessionDate: 'Jan 31' },
  { id: 't9', text: 'Practice TIPP technique daily', completed: true, sessionId: 's2', sessionDate: 'Jan 17' }
];

export const progressMetrics: ProgressMetric[] = [
  {
    title: 'Mood Trends',
    description: 'Session-by-session mood tracking',
    emoji: '📈',
    insight: '+30% mood improvement over 10 sessions',
    chartData: [
      { session: 'S1', mood: 4 },
      { session: 'S2', mood: 4.5 },
      { session: 'S3', mood: 3 },
      { session: 'S4', mood: 3.5 },
      { session: 'S5', mood: 5 },
      { session: 'S6', mood: 3 },
      { session: 'S7', mood: 5.5 },
      { session: 'S8', mood: 5 },
      { session: 'S9', mood: 7 },
      { session: 'S10', mood: 7.5 }
    ]
  },
  {
    title: 'Homework Impact',
    description: 'Correlation between task completion and mood',
    emoji: '📊',
    insight: '85% completion rate correlates with 40% mood boost',
    chartData: [
      { week: 'Week 1-2', completion: 50, mood: 4 },
      { week: 'Week 3-4', completion: 75, mood: 5 },
      { week: 'Week 5-6', completion: 60, mood: 4.5 },
      { week: 'Week 7-8', completion: 90, mood: 6.5 },
      { week: 'Week 9-10', completion: 85, mood: 7 }
    ]
  },
  {
    title: 'Session Consistency',
    description: 'Weekly session attendance pattern',
    emoji: '📅',
    insight: '100% attendance over 10 weeks - exceptional commitment',
    chartData: [
      { week: 'W1', attended: 1 },
      { week: 'W2', attended: 1 },
      { week: 'W3', attended: 1 },
      { week: 'W4', attended: 1 },
      { week: 'W5', attended: 1 },
      { week: 'W6', attended: 1 },
      { week: 'W7', attended: 1 },
      { week: 'W8', attended: 1 },
      { week: 'W9', attended: 1 },
      { week: 'W10', attended: 1 }
    ]
  },
  {
    title: 'Strategy Effectiveness',
    description: 'Which therapeutic techniques work best',
    emoji: '🎯',
    insight: 'Laddering technique showed highest effectiveness rating',
    chartData: [
      { strategy: 'Laddering', effectiveness: 95 },
      { strategy: 'DBT Skills', effectiveness: 85 },
      { strategy: 'Assertiveness', effectiveness: 80 },
      { strategy: 'Sleep Hygiene', effectiveness: 75 },
      { strategy: 'Cognitive Restr.', effectiveness: 70 }
    ]
  }
];

export const initialChatMessages: ChatMessage[] = [
  {
    id: 'c1',
    role: 'assistant',
    content: "Hi! I'm Dobby, your therapy companion. I'm here to help you prepare for sessions, answer questions, or pass messages to your therapist. How can I help you today?",
    timestamp: new Date()
  }
];

export const chatPrompts: string[] = [
  'Why does my mood drop after family visits?',
  'Help me prep to discuss boundaries...',
  'Explain the TIPP technique again',
  'What should I bring up in next session?',
  'I had a panic attack - what do I do?',
  'Send message to my therapist'
];

/**
 * @deprecated Use unifiedTimeline instead for mixed event support
 */
export const timelineData: TimelineEntry[] = sessions.map(s => ({
  sessionId: s.id,
  date: s.date,
  duration: s.duration,
  topic: s.topics.join(', '),
  strategy: s.strategy,
  mood: s.mood,
  milestone: s.milestone
}));

// ============================================
// Major Events (from Chatbot, AI-detected)
// ============================================

/**
 * Major events detected from chatbot conversations.
 * These are significant life events that the AI identified
 * and the patient confirmed should appear on their timeline.
 */
export const majorEvents: MajorEventEntry[] = [
  {
    id: 'me1',
    eventType: 'major_event',
    date: 'Dec 14',
    timestamp: new Date('2024-12-14'),
    title: 'Got promoted at work',
    summary: 'Received a promotion to Senior Developer role after successfully leading the Q4 project. This represents growth in managing work stress and perfectionism.',
    chatContext: 'Patient shared excitement about promotion while also expressing anxiety about increased responsibilities. Discussed how therapy strategies helped manage imposter syndrome during the interview process.',
    relatedSessionId: 's8',  // Dec 3 - Work stress session
    confirmedByPatient: true,
    reflection: undefined
  },
  {
    id: 'me2',
    eventType: 'major_event',
    date: 'Nov 22',
    timestamp: new Date('2024-11-22'),
    title: 'Set boundary with mother about holidays',
    summary: 'Had a difficult but successful conversation with mother about limiting holiday visit duration. Applied assertiveness techniques from therapy.',
    chatContext: 'Patient reported feeling anxious before the conversation but proud afterward. Used I-statements and stayed calm when mother initially pushed back.',
    relatedSessionId: 's6',  // Nov 19 - Depression/Isolation (closest session)
    confirmedByPatient: true,
    reflection: 'This was so hard but I did it! Mom was upset at first but she understood eventually.'
  },
  {
    id: 'me3',
    eventType: 'major_event',
    date: 'Nov 8',
    timestamp: new Date('2024-11-08'),
    title: 'Started daily meditation practice',
    summary: 'Committed to 10-minute daily meditation after discussing coping strategies. Has maintained the practice for 3 weeks.',
    chatContext: 'Patient asked about additional self-care practices. AI suggested meditation as complement to TIPP technique. Patient reported trying it and finding it helpful for morning anxiety.',
    relatedSessionId: 's5',  // Nov 12 - Active listening/communication (closest)
    confirmedByPatient: true,
    reflection: undefined
  },
  {
    id: 'me4',
    eventType: 'major_event',
    date: 'Oct 25',
    timestamp: new Date('2024-10-25'),
    title: 'First panic-free week in months',
    summary: 'Went an entire week without a panic attack for the first time since starting therapy. TIPP and grounding techniques proving effective.',
    chatContext: 'Patient excitedly shared this milestone in chat. Discussed what contributed to success and how to maintain progress.',
    relatedSessionId: 's2',  // Oct 22 - DBT skills/TIPP
    confirmedByPatient: true,
    reflection: 'I never thought I could do this. The techniques actually work when I use them consistently.'
  }
];

// ============================================
// Unified Timeline (Sessions + Major Events)
// ============================================

/**
 * Helper to convert Session to SessionTimelineEvent
 */
const sessionToTimelineEvent = (s: Session): SessionTimelineEvent => ({
  id: `session-${s.id}`,
  eventType: 'session',
  date: s.date,
  timestamp: parseDateString(s.date),
  sessionId: s.id,
  duration: s.duration,
  topic: s.topics.join(', '),
  strategy: s.strategy,
  mood: s.mood,
  milestone: s.milestone
});

/**
 * Parse display date string to Date object for sorting.
 * Assumes current year (2024) for dates like "Dec 17"
 */
function parseDateString(dateStr: string): Date {
  const months: Record<string, number> = {
    'Jan': 0, 'Feb': 1, 'Mar': 2, 'Apr': 3, 'May': 4, 'Jun': 5,
    'Jul': 6, 'Aug': 7, 'Sep': 8, 'Oct': 9, 'Nov': 10, 'Dec': 11
  };
  const parts = dateStr.split(' ');
  const month = months[parts[0]];
  const day = parseInt(parts[1], 10);
  return new Date(2024, month, day);
}

/**
 * Unified timeline combining sessions and major events.
 * Sorted chronologically (newest first).
 */
export const unifiedTimeline: TimelineEvent[] = [
  ...sessions.map(sessionToTimelineEvent),
  ...majorEvents
].sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());

export const notesGoalsContent = {
  summary: "Based on 10 sessions, you've made remarkable progress in your therapeutic journey.",
  achievements: [
    'Reduced depression symptoms by 67%',
    'Mastered 3 core coping strategies (TIPP, laddering, assertiveness)',
    'Identified primary pattern: work stress triggers family conflict',
    'Successfully set boundaries with family members',
    'Achieved breakthrough self-compassion insight'
  ],
  currentFocus: ['Boundary maintenance', 'Self-compassion practice', 'Perfectionism at work'],
  sections: [
    {
      title: 'Clinical Progress',
      content: 'Significant improvement in depressive symptoms (67% reduction). Mood stability has increased, with fewer low episodes. Panic attack frequency reduced from 3-4/week to less than 1/week. Sleep quality improved by 40%.'
    },
    {
      title: 'Therapeutic Strategies Learned',
      content: 'Successfully integrated TIPP technique for crisis management, laddering technique for self-worth exploration, assertiveness training for boundary-setting, cognitive restructuring for perfectionism, and behavioral activation for depression management.'
    },
    {
      title: 'Identified Patterns',
      content: 'Core pattern: Work-related stress and perfectionism trigger family conflict and people-pleasing behaviors. Childhood neglect experiences contribute to adult self-worth challenges. Avoidance behaviors temporarily reduce anxiety but increase long-term distress.'
    },
    {
      title: 'Current Treatment Focus',
      content: 'Maintaining healthy boundaries with family, continuing self-compassion practice, addressing workplace perfectionism, trauma processing (childhood experiences), relationship communication skills.'
    },
    {
      title: 'Long-term Goals',
      content: 'Sustain mood improvements, develop consistent self-care routine, build authentic relationships without people-pleasing, advance career without perfectionism-driven burnout, process trauma memories safely.'
    }
  ]
};

export const therapistBridgeContent = {
  nextSessionTopics: [
    'Progress on family boundaries this week',
    'Workplace perfectionism - new strategies needed?',
    'Romantic relationship dynamics'
  ],
  shareProgress: [
    'Completed 3-week sleep hygiene plan successfully',
    'Used assertiveness skills with mother',
    'Maintained daily walking habit for 2 weeks',
    'Applied self-compassion during difficult moment'
  ],
  sessionPrep: [
    'Review anxiety journal entries from past week',
    'Bring up work presentation anxiety',
    'Discuss upcoming family holiday stress',
    'Ask about couples therapy recommendation'
  ]
};
