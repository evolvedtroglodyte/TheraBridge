"""
Prose Analysis Generator Service

Converts structured deep_analysis JSON into patient-facing prose narrative.
Uses GPT-5.2 to generate 500-750 word compassionate clinical summary.

Output: 5 flowing paragraphs addressing patient directly, combining:
- Empowering therapist letter tone
- Clinical precision and terminology
- Accessible language with therapeutic jargon
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import openai
import os
import logging
import time

from app.config.model_config import get_model_name, track_generation_cost, GenerationCost

logger = logging.getLogger(__name__)


@dataclass
class ProseAnalysis:
    """Patient-facing prose narrative generated from deep analysis"""
    session_id: str
    prose_text: str  # 500-750 word narrative
    word_count: int
    paragraph_count: int
    confidence_score: float  # Inherited from deep_analysis
    generated_at: datetime
    cost_info: Optional[GenerationCost] = None  # Cost tracking for this generation


class ProseGenerator:
    """
    AI-powered prose generation for therapy session analysis.

    Converts structured DeepAnalysis JSON into flowing prose narrative
    that combines compassionate tone with clinical expertise.
    """

    def __init__(self, api_key: Optional[str] = None, override_model: Optional[str] = None):
        """
        Initialize the prose generator.

        Args:
            api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
            override_model: Optional model override for testing (default: gpt-5.2)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required for prose generation")

        openai.api_key = self.api_key
        self.model = get_model_name("deep_analysis", override_model=override_model)  # Uses gpt-5.2

    async def generate_prose(
        self,
        session_id: str,
        deep_analysis: Dict[str, Any],
        confidence_score: float
    ) -> ProseAnalysis:
        """
        Generate patient-facing prose from structured deep analysis.

        Args:
            session_id: Session UUID
            deep_analysis: Complete structured analysis (from deep_analyzer.py)
            confidence_score: Analysis confidence (0.0 - 1.0)

        Returns:
            ProseAnalysis with 500-750 word narrative
        """
        logger.info(f"📝 Generating prose analysis for session {session_id}")

        # Create prose generation prompt
        prompt = self._create_prose_prompt(deep_analysis)

        # Call OpenAI API (GPT-5.2)
        # NOTE: GPT-5 series does NOT support custom temperature
        try:
            start_time = time.time()
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Track cost and timing
            cost_info = track_generation_cost(
                response=response,
                task="prose_generation",
                model=self.model,
                start_time=start_time,
                session_id=session_id
            )

            prose_text = response.choices[0].message.content.strip()

            # Validate output
            word_count = len(prose_text.split())
            paragraph_count = len([p for p in prose_text.split('\n\n') if p.strip()])

            if word_count < 400 or word_count > 900:
                logger.warning(f"Prose word count ({word_count}) outside target range 500-750")

            if paragraph_count != 5:
                logger.warning(f"Prose has {paragraph_count} paragraphs, expected 5")

            analysis = ProseAnalysis(
                session_id=session_id,
                prose_text=prose_text,
                word_count=word_count,
                paragraph_count=paragraph_count,
                confidence_score=confidence_score,
                generated_at=datetime.utcnow(),
                cost_info=cost_info
            )

            logger.info(f"✓ Prose generated: {word_count} words, {paragraph_count} paragraphs")

            return analysis

        except Exception as e:
            logger.error(f"Prose generation failed for session {session_id}: {e}")
            raise Exception(f"Prose generation failed: {str(e)}")

    def _get_system_prompt(self) -> str:
        """System prompt defining prose generation guidelines."""
        return """You are an expert clinical psychologist writing patient-facing session summaries.

Your task is to convert structured therapeutic analysis into a warm, encouraging prose narrative
that combines the compassionate tone of a therapist's letter with the precision of a clinical summary.

**YOUR ROLE:**
- Write directly to the patient using second person ("you", "your")
- Balance empathy with clinical expertise
- Use therapeutic terminology naturally (show industry knowledge)
- Make complex insights accessible and actionable
- Maintain professional warmth throughout

**OUTPUT REQUIREMENTS:**

**Length:** 500-750 words total (strict)

**Structure:** 5 flowing paragraphs (no headings or labels):
1. **Session Overview & Context** - Introduce the session with mood/emotional tone
2. **Key Insights & Realizations** - Highlight breakthroughs and patterns
3. **Skill Development & Progress** - Discuss coping skills and growth
4. **Therapeutic Progress** - Address relationship quality and engagement
5. **Next Steps & Encouragement** - Provide actionable recommendations with hope

**Tone Guidelines:**
- Compassionate and validating (acknowledge struggles genuinely)
- Empowering (emphasize agency and strengths)
- Clinical precision (use proper therapeutic terms: "cognitive restructuring", "affect regulation", "therapeutic alliance")
- Accessible (explain complex concepts clearly)
- Hopeful (end with encouragement and forward momentum)

**Language Choices:**
- Direct address: "You demonstrated...", "In this session, you..."
- Present therapeutic techniques accurately: "We explored dialectical thinking", "You practiced opposite action"
- Balance validation with growth: "While anxiety persisted, you showed remarkable courage in..."
- Specific evidence: Reference actual session moments when possible

**What to AVOID:**
- Paragraph headings or section labels
- Overly clinical distance ("The patient exhibited...")
- Jargon without context ("Use DBT skills" → "Use the DBT distress tolerance skills we practiced")
- Generic platitudes ("You're doing great!")
- Bullet points or lists (pure prose only)

**Quality Markers:**
- Reads like a personalized letter from therapist
- Demonstrates deep clinical knowledge
- Feels supportive without being patronizing
- Specific to this patient's unique journey
- Natural paragraph flow with clear transitions

Return ONLY the prose text (no JSON, no formatting markers, no metadata).
Separate paragraphs with double newlines."""

    def _create_prose_prompt(self, deep_analysis: Dict[str, Any]) -> str:
        """Create the prose generation prompt from structured analysis."""
        # Extract structured components
        progress = deep_analysis.get("progress_indicators", {})
        insights = deep_analysis.get("therapeutic_insights", {})
        skills = deep_analysis.get("coping_skills", {})
        relationship = deep_analysis.get("therapeutic_relationship", {})
        recommendations = deep_analysis.get("recommendations", {})

        return f"""Convert the following structured therapeutic analysis into a 500-750 word prose narrative.

Create 5 flowing paragraphs that address: session overview, key insights, skill development,
therapeutic progress, and next steps. Adapt the emphasis based on what's most clinically
relevant in this specific session.

**STRUCTURED ANALYSIS DATA:**

**Progress Indicators:**
- Symptom Reduction: {progress.get('symptom_reduction', {})}
- Skill Development: {progress.get('skill_development', [])}
- Goal Progress: {progress.get('goal_progress', [])}
- Behavioral Changes: {progress.get('behavioral_changes', [])}

**Therapeutic Insights:**
- Key Realizations: {insights.get('key_realizations', [])}
- Patterns: {insights.get('patterns', [])}
- Growth Areas: {insights.get('growth_areas', [])}
- Strengths: {insights.get('strengths', [])}

**Coping Skills:**
- Learned: {skills.get('learned', [])}
- Proficiency: {skills.get('proficiency', {})}
- Practice Recommendations: {skills.get('practice_recommendations', [])}

**Therapeutic Relationship:**
- Engagement: {relationship.get('engagement_level', 'N/A')} - {relationship.get('engagement_evidence', '')}
- Openness: {relationship.get('openness', 'N/A')} - {relationship.get('openness_evidence', '')}
- Alliance: {relationship.get('alliance_strength', 'N/A')} - {relationship.get('alliance_evidence', '')}

**Recommendations:**
- Practices: {recommendations.get('practices', [])}
- Resources: {recommendations.get('resources', [])}
- Reflection Prompts: {recommendations.get('reflection_prompts', [])}

---

**INSTRUCTIONS:**

Write a compassionate, clinically-informed prose narrative that integrates all the above insights.

Remember:
- 500-750 words total
- 5 paragraphs (no headings)
- Address the patient directly
- Use therapeutic terminology naturally
- Balance empathy with expertise
- End with hope and encouragement

Begin writing now:"""


# Convenience function
async def generate_prose_from_analysis(
    session_id: str,
    deep_analysis: Dict[str, Any],
    confidence_score: float,
    api_key: Optional[str] = None
) -> ProseAnalysis:
    """
    Convenience function to generate prose from deep analysis.

    Args:
        session_id: Session UUID
        deep_analysis: Structured analysis from deep_analyzer.py
        confidence_score: Analysis confidence
        api_key: Optional OpenAI API key

    Returns:
        ProseAnalysis object
    """
    generator = ProseGenerator(api_key=api_key)
    return await generator.generate_prose(session_id, deep_analysis, confidence_score)
