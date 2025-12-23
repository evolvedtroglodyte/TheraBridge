'use client';

/**
 * Deep Analysis Section Component
 *
 * Displays comprehensive AI-generated clinical analysis including:
 * - Progress indicators (symptom reduction, skill development, goals)
 * - Therapeutic insights (realizations, patterns, growth, strengths)
 * - Coping skills (learned, proficiency, recommendations)
 * - Therapeutic relationship quality
 * - Patient-facing recommendations
 */

import { Brain, TrendingUp, Lightbulb, Wrench, Heart, CheckCircle2, Target, Sparkles } from 'lucide-react';

// Font families
const fontSans = '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
const fontSerif = '"Crimson Pro", Georgia, serif';

interface ProgressIndicator {
  symptom_reduction?: {
    detected: boolean;
    description: string;
    confidence: number;
  };
  skill_development?: Array<{
    skill: string;
    proficiency: 'beginner' | 'developing' | 'proficient';
    evidence: string;
  }>;
  goal_progress?: Array<{
    goal: string;
    status: 'on_track' | 'needs_attention' | 'achieved';
    evidence: string;
  }>;
  behavioral_changes?: string[];
}

interface TherapeuticInsights {
  key_realizations: string[];
  patterns: string[];
  growth_areas: string[];
  strengths: string[];
}

interface CopingSkills {
  learned: string[];
  proficiency: Record<string, 'beginner' | 'developing' | 'proficient'>;
  practice_recommendations: string[];
}

interface TherapeuticRelationship {
  engagement_level: 'low' | 'moderate' | 'high';
  engagement_evidence: string;
  openness: 'guarded' | 'somewhat_open' | 'very_open';
  openness_evidence: string;
  alliance_strength: 'weak' | 'developing' | 'strong';
  alliance_evidence: string;
}

interface Recommendations {
  practices: string[];
  resources: string[];
  reflection_prompts: string[];
}

export interface DeepAnalysis {
  progress_indicators: ProgressIndicator;
  therapeutic_insights: TherapeuticInsights;
  coping_skills: CopingSkills;
  therapeutic_relationship: TherapeuticRelationship;
  recommendations: Recommendations;
  confidence_score: number;
  analyzed_at: string;
}

interface DeepAnalysisSectionProps {
  analysis: DeepAnalysis;
  confidence: number;
}

export function DeepAnalysisSection({ analysis, confidence }: DeepAnalysisSectionProps) {
  const { progress_indicators, therapeutic_insights, coping_skills, therapeutic_relationship, recommendations } = analysis;

  return (
    <div className="mb-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 style={{ fontFamily: fontSans }} className="text-xl font-semibold text-gray-800 dark:text-gray-200">
              Deep Clinical Analysis
            </h3>
            <p style={{ fontFamily: fontSans }} className="text-xs text-gray-500 dark:text-gray-400">
              AI-powered insights • {Math.round(confidence * 100)}% confidence
            </p>
          </div>
        </div>
      </div>

      {/* Progress Indicators */}
      <ProgressIndicatorsCard data={progress_indicators} />

      {/* Therapeutic Insights */}
      <TherapeuticInsightsCard data={therapeutic_insights} />

      {/* Coping Skills */}
      <CopingSkillsCard data={coping_skills} />

      {/* Therapeutic Relationship */}
      <TherapeuticRelationshipCard data={therapeutic_relationship} />

      {/* Recommendations */}
      <RecommendationsCard data={recommendations} />
    </div>
  );
}

// =============================================================================
// Sub-components
// =============================================================================

function ProgressIndicatorsCard({ data }: { data: ProgressIndicator }) {
  return (
    <div className="mb-4 p-4 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-xl border border-green-200 dark:border-green-800">
      <div className="flex items-center gap-2 mb-3">
        <TrendingUp className="w-5 h-5 text-green-600 dark:text-green-400" />
        <h4 style={{ fontFamily: fontSans }} className="text-sm font-semibold text-green-900 dark:text-green-400 uppercase tracking-wide">
          Your Progress
        </h4>
      </div>

      {/* Symptom Reduction */}
      {data.symptom_reduction?.detected && (
        <div className="mb-3 p-3 bg-white dark:bg-gray-800/50 rounded-lg">
          <div className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
            <div>
              <p style={{ fontFamily: fontSans }} className="text-xs font-semibold text-green-700 dark:text-green-400 mb-1">
                Symptom Improvement Detected
              </p>
              <p style={{ fontFamily: fontSerif }} className="text-sm text-gray-700 dark:text-gray-300">
                {data.symptom_reduction.description}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Skill Development */}
      {data.skill_development && data.skill_development.length > 0 && (
        <div className="mb-3">
          <p style={{ fontFamily: fontSans }} className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
            Skills You're Building
          </p>
          <div className="space-y-2">
            {data.skill_development.map((skill, idx) => (
              <div key={idx} className="p-2 bg-white dark:bg-gray-800/50 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-lg">
                    {skill.proficiency === 'beginner' ? '🌱' : skill.proficiency === 'developing' ? '🌿' : '🌳'}
                  </span>
                  <p style={{ fontFamily: fontSans }} className="text-sm font-medium text-gray-800 dark:text-gray-200">
                    {skill.skill}
                  </p>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 capitalize">
                    {skill.proficiency}
                  </span>
                </div>
                <p style={{ fontFamily: fontSerif }} className="text-xs text-gray-600 dark:text-gray-400 pl-7">
                  {skill.evidence}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Goal Progress */}
      {data.goal_progress && data.goal_progress.length > 0 && (
        <div className="mb-3">
          <p style={{ fontFamily: fontSans }} className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
            Goal Progress
          </p>
          <div className="space-y-2">
            {data.goal_progress.map((goal, idx) => (
              <div key={idx} className="p-2 bg-white dark:bg-gray-800/50 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-lg">
                    {goal.status === 'achieved' ? '✅' : goal.status === 'on_track' ? '🔄' : '⚠️'}
                  </span>
                  <p style={{ fontFamily: fontSans }} className="text-sm font-medium text-gray-800 dark:text-gray-200">
                    {goal.goal}
                  </p>
                </div>
                <p style={{ fontFamily: fontSerif }} className="text-xs text-gray-600 dark:text-gray-400 pl-7">
                  {goal.evidence}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Behavioral Changes */}
      {data.behavioral_changes && data.behavioral_changes.length > 0 && (
        <div>
          <p style={{ fontFamily: fontSans }} className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
            Positive Changes
          </p>
          <ul className="space-y-1">
            {data.behavioral_changes.map((change, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                <span className="w-1.5 h-1.5 rounded-full bg-green-500 mt-2 flex-shrink-0" />
                <span style={{ fontFamily: fontSerif }}>{change}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function TherapeuticInsightsCard({ data }: { data: TherapeuticInsights }) {
  return (
    <div className="mb-4 p-4 bg-gradient-to-br from-yellow-50 to-amber-50 dark:from-yellow-900/20 dark:to-amber-900/20 rounded-xl border border-yellow-200 dark:border-yellow-800">
      <div className="flex items-center gap-2 mb-3">
        <Lightbulb className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
        <h4 style={{ fontFamily: fontSans }} className="text-sm font-semibold text-yellow-900 dark:text-yellow-400 uppercase tracking-wide">
          Key Insights
        </h4>
      </div>

      {/* Key Realizations */}
      {data.key_realizations.length > 0 && (
        <div className="mb-3">
          <p style={{ fontFamily: fontSans }} className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
            💡 Realizations
          </p>
          <ul className="space-y-2">
            {data.key_realizations.map((realization, idx) => (
              <li key={idx} className="p-2 bg-white dark:bg-gray-800/50 rounded-lg">
                <p style={{ fontFamily: fontSerif }} className="text-sm text-gray-700 dark:text-gray-300">
                  {realization}
                </p>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Patterns */}
      {data.patterns.length > 0 && (
        <div className="mb-3">
          <p style={{ fontFamily: fontSans }} className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
            🔗 Patterns Emerging
          </p>
          <ul className="space-y-2">
            {data.patterns.map((pattern, idx) => (
              <li key={idx} className="p-2 bg-white dark:bg-gray-800/50 rounded-lg">
                <p style={{ fontFamily: fontSerif }} className="text-sm text-gray-700 dark:text-gray-300">
                  {pattern}
                </p>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Growth Areas */}
      {data.growth_areas.length > 0 && (
        <div className="mb-3">
          <p style={{ fontFamily: fontSans }} className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
            🌱 Areas of Growth
          </p>
          <ul className="space-y-1">
            {data.growth_areas.map((area, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                <span className="w-1.5 h-1.5 rounded-full bg-yellow-500 mt-2 flex-shrink-0" />
                <span style={{ fontFamily: fontSerif }}>{area}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Strengths */}
      {data.strengths.length > 0 && (
        <div>
          <p style={{ fontFamily: fontSans }} className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
            💪 Strengths You Demonstrated
          </p>
          <ul className="space-y-1">
            {data.strengths.map((strength, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-2 flex-shrink-0" />
                <span style={{ fontFamily: fontSerif }}>{strength}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function CopingSkillsCard({ data }: { data: CopingSkills }) {
  return (
    <div className="mb-4 p-4 bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20 rounded-xl border border-blue-200 dark:border-blue-800">
      <div className="flex items-center gap-2 mb-3">
        <Wrench className="w-5 h-5 text-blue-600 dark:text-blue-400" />
        <h4 style={{ fontFamily: fontSans }} className="text-sm font-semibold text-blue-900 dark:text-blue-400 uppercase tracking-wide">
          Coping Skills
        </h4>
      </div>

      {/* Skills Learned */}
      {data.learned.length > 0 && (
        <div className="mb-3">
          <p style={{ fontFamily: fontSans }} className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
            📚 Skills You're Learning
          </p>
          <div className="flex flex-wrap gap-2">
            {data.learned.map((skill, idx) => {
              const proficiency = data.proficiency[skill.replace(/\s+/g, '_')] || 'beginner';
              return (
                <span
                  key={idx}
                  className="px-3 py-1.5 bg-white dark:bg-gray-800/50 rounded-full text-xs font-medium text-blue-700 dark:text-blue-400 border border-blue-200 dark:border-blue-800"
                >
                  {skill}
                  <span className="ml-1 text-[10px] opacity-75">
                    ({proficiency === 'beginner' ? '🌱' : proficiency === 'developing' ? '🌿' : '🌳'})
                  </span>
                </span>
              );
            })}
          </div>
        </div>
      )}

      {/* Practice Recommendations */}
      {data.practice_recommendations.length > 0 && (
        <div>
          <p style={{ fontFamily: fontSans }} className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
            → Practice This Week
          </p>
          <ul className="space-y-2">
            {data.practice_recommendations.map((rec, idx) => (
              <li key={idx} className="p-2 bg-white dark:bg-gray-800/50 rounded-lg">
                <p style={{ fontFamily: fontSerif }} className="text-sm text-gray-700 dark:text-gray-300">
                  {rec}
                </p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function TherapeuticRelationshipCard({ data }: { data: TherapeuticRelationship }) {
  return (
    <div className="mb-4 p-4 bg-gradient-to-br from-pink-50 to-rose-50 dark:from-pink-900/20 dark:to-rose-900/20 rounded-xl border border-pink-200 dark:border-pink-800">
      <div className="flex items-center gap-2 mb-3">
        <Heart className="w-5 h-5 text-pink-600 dark:text-pink-400" />
        <h4 style={{ fontFamily: fontSans }} className="text-sm font-semibold text-pink-900 dark:text-pink-400 uppercase tracking-wide">
          Therapeutic Connection
        </h4>
      </div>

      <div className="space-y-3">
        {/* Engagement */}
        <div className="p-3 bg-white dark:bg-gray-800/50 rounded-lg">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-lg">
              {data.engagement_level === 'high' ? '🔥' : data.engagement_level === 'moderate' ? '⚡' : '💤'}
            </span>
            <p style={{ fontFamily: fontSans }} className="text-sm font-semibold text-gray-800 dark:text-gray-200">
              Engagement: <span className="capitalize">{data.engagement_level}</span>
            </p>
          </div>
          <p style={{ fontFamily: fontSerif }} className="text-xs text-gray-600 dark:text-gray-400 pl-7">
            {data.engagement_evidence}
          </p>
        </div>

        {/* Openness */}
        <div className="p-3 bg-white dark:bg-gray-800/50 rounded-lg">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-lg">
              {data.openness === 'very_open' ? '🌊' : data.openness === 'somewhat_open' ? '🌤️' : '🛡️'}
            </span>
            <p style={{ fontFamily: fontSans }} className="text-sm font-semibold text-gray-800 dark:text-gray-200">
              Openness: <span className="capitalize">{data.openness.replace('_', ' ')}</span>
            </p>
          </div>
          <p style={{ fontFamily: fontSerif }} className="text-xs text-gray-600 dark:text-gray-400 pl-7">
            {data.openness_evidence}
          </p>
        </div>

        {/* Alliance Strength */}
        <div className="p-3 bg-white dark:bg-gray-800/50 rounded-lg">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-lg">
              {data.alliance_strength === 'strong' ? '💎' : data.alliance_strength === 'developing' ? '🌿' : '🌱'}
            </span>
            <p style={{ fontFamily: fontSans }} className="text-sm font-semibold text-gray-800 dark:text-gray-200">
              Alliance: <span className="capitalize">{data.alliance_strength}</span>
            </p>
          </div>
          <p style={{ fontFamily: fontSerif }} className="text-xs text-gray-600 dark:text-gray-400 pl-7">
            {data.alliance_evidence}
          </p>
        </div>
      </div>
    </div>
  );
}

function RecommendationsCard({ data }: { data: Recommendations }) {
  return (
    <div className="p-4 bg-gradient-to-br from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20 rounded-xl border border-purple-200 dark:border-purple-800">
      <div className="flex items-center gap-2 mb-3">
        <Target className="w-5 h-5 text-purple-600 dark:text-purple-400" />
        <h4 style={{ fontFamily: fontSans }} className="text-sm font-semibold text-purple-900 dark:text-purple-400 uppercase tracking-wide">
          Between Sessions
        </h4>
      </div>

      {/* Practices */}
      {data.practices.length > 0 && (
        <div className="mb-3">
          <p style={{ fontFamily: fontSans }} className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
            ✓ Try These Practices
          </p>
          <ul className="space-y-2">
            {data.practices.map((practice, idx) => (
              <li key={idx} className="p-2 bg-white dark:bg-gray-800/50 rounded-lg">
                <p style={{ fontFamily: fontSerif }} className="text-sm text-gray-700 dark:text-gray-300">
                  {practice}
                </p>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Resources */}
      {data.resources.length > 0 && (
        <div className="mb-3">
          <p style={{ fontFamily: fontSans }} className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
            📖 Helpful Resources
          </p>
          <ul className="space-y-1">
            {data.resources.map((resource, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                <span className="w-1.5 h-1.5 rounded-full bg-purple-500 mt-2 flex-shrink-0" />
                <span style={{ fontFamily: fontSerif }}>{resource}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Reflection Prompts */}
      {data.reflection_prompts.length > 0 && (
        <div>
          <p style={{ fontFamily: fontSans }} className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
            💭 Journal Prompts
          </p>
          <ul className="space-y-2">
            {data.reflection_prompts.map((prompt, idx) => (
              <li key={idx} className="p-2 bg-white dark:bg-gray-800/50 rounded-lg">
                <p style={{ fontFamily: fontSerif }} className="text-sm italic text-gray-700 dark:text-gray-300">
                  {prompt}
                </p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
