/**
 * Mock data for TherapyBridge Dashboard demo
 * - 10 therapy sessions with realistic content
 * - Tasks, milestones, and progress metrics
 * - Timeline and chat conversation data
 */

import { Session, Task, ProgressMetric, ChatMessage, TimelineEntry } from './types';

export const sessions: Session[] = [
  {
    id: 's10',
    date: 'Dec 17',
    duration: '50m',
    therapist: 'Dr. Sarah Chen',
    mood: 'positive',
    topics: ['Boundaries', 'Family dynamics'],
    strategy: 'Assertiveness training',
    actions: ['Set clear boundaries', 'Practice saying no'],
    transcript: [
      { speaker: 'Therapist', text: 'How did the boundary-setting go this week?' },
      { speaker: 'Patient', text: "It was tough but I actually said no to my mom's request to babysit on my work day." },
      { speaker: 'Therapist', text: 'That\'s a significant step. How did it feel?' },
      { speaker: 'Patient', text: 'Scary at first, but then relieving. Like a weight lifted.' }
    ],
    patientSummary: 'Made breakthrough progress on setting boundaries with family. Successfully practiced assertiveness techniques learned in previous sessions.'
  },
  {
    id: 's9',
    date: 'Dec 10',
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
      { speaker: 'Therapist', text: 'Tell me about the compassion exercise you tried.' },
      { speaker: 'Patient', text: 'I wrote that letter to my younger self. I cried for an hour but it helped me realize I was never the problem.' },
      { speaker: 'Therapist', text: 'That\'s a profound realization. How does that shift how you see yourself now?' },
      { speaker: 'Patient', text: 'I think... I think I deserve kindness. Even from myself.' }
    ],
    patientSummary: 'Breakthrough session with emotional release. Patient connected childhood neglect to adult self-worth issues and demonstrated genuine self-compassion.'
  },
  {
    id: 's8',
    date: 'Dec 3',
    duration: '48m',
    therapist: 'Dr. Sarah Chen',
    mood: 'neutral',
    topics: ['Work stress', 'Perfectionism'],
    strategy: 'Cognitive restructuring',
    actions: ['Challenge catastrophizing', 'Priority matrix exercise'],
    transcript: [
      { speaker: 'Therapist', text: 'What happened with the project deadline?' },
      { speaker: 'Patient', text: 'I stayed late every night but still felt like it wasn\'t good enough.' },
      { speaker: 'Therapist', text: 'Let\'s examine that thought - what\'s the evidence it wasn\'t good enough?' },
      { speaker: 'Patient', text: 'Well... my boss said it was excellent. But I saw all the flaws.' }
    ],
    patientSummary: 'Identified perfectionism pattern at work. Began recognizing cognitive distortions around performance standards.'
  },
  {
    id: 's7',
    date: 'Nov 26',
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
    date: 'Nov 19',
    duration: '50m',
    therapist: 'Dr. Sarah Chen',
    mood: 'low',
    topics: ['Depression episode', 'Isolation'],
    strategy: 'Behavioral activation',
    actions: ['Daily walk commitment', 'Social contact plan'],
    transcript: [
      { speaker: 'Therapist', text: 'How has your mood been this week?' },
      { speaker: 'Patient', text: 'Really low. I cancelled everything and stayed in bed most of Saturday.' },
      { speaker: 'Therapist', text: 'I appreciate you sharing that. What\'s one small thing you could do today?' },
      { speaker: 'Patient', text: 'Maybe... maybe just walk to the mailbox.' }
    ],
    patientSummary: 'Experiencing depressive episode. Developed behavioral activation plan starting with minimal achievable goals.'
  },
  {
    id: 's5',
    date: 'Nov 12',
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
    date: 'Nov 5',
    duration: '50m',
    therapist: 'Dr. Sarah Chen',
    mood: 'low',
    topics: ['Childhood trauma', 'Trust issues'],
    strategy: 'Trauma-focused CBT',
    actions: ['Grounding techniques', 'Safety plan review'],
    transcript: [
      { speaker: 'Therapist', text: 'You mentioned feeling triggered this week. Can you tell me more?' },
      { speaker: 'Patient', text: 'My partner raised his voice and I just... froze. Like I was a kid again.' },
      { speaker: 'Therapist', text: 'Thank you for trusting me with that. Let\'s practice the grounding technique we discussed.' }
    ],
    patientSummary: 'Processing childhood trauma memories. Experiencing flashback triggers. Reinforced grounding and safety strategies.'
  },
  {
    id: 's3',
    date: 'Oct 29',
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
    date: 'Oct 22',
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
    date: 'Oct 15',
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
  { id: 't1', text: 'Practice saying no to one request', completed: true, sessionId: 's10', sessionDate: 'Dec 17' },
  { id: 't2', text: 'Write compassion letter to younger self', completed: true, sessionId: 's9', sessionDate: 'Dec 10' },
  { id: 't3', text: 'Daily 10-minute walk', completed: true, sessionId: 's6', sessionDate: 'Nov 19' },
  { id: 't4', text: 'Challenge one catastrophic thought per day', completed: false, sessionId: 's8', sessionDate: 'Dec 3' },
  { id: 't5', text: 'Maintain sleep schedule (10pm bedtime)', completed: false, sessionId: 's7', sessionDate: 'Nov 26' },
  { id: 't6', text: 'Practice I-statements with partner', completed: false, sessionId: 's5', sessionDate: 'Nov 12' },
  { id: 't7', text: 'Grounding exercise when triggered', completed: true, sessionId: 's4', sessionDate: 'Nov 5' },
  { id: 't8', text: 'Keep anxiety journal', completed: false, sessionId: 's3', sessionDate: 'Oct 29' },
  { id: 't9', text: 'Practice TIPP technique daily', completed: true, sessionId: 's2', sessionDate: 'Oct 22' }
];

export const progressMetrics: ProgressMetric[] = [
  {
    title: 'Mood Trend',
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

export const timelineData: TimelineEntry[] = sessions.map(s => ({
  sessionId: s.id,
  date: s.date,
  topic: s.topics[0],
  mood: s.mood,
  milestone: s.milestone
}));

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
