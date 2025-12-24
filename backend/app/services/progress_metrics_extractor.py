"""
Progress Metrics Extraction Service

Extracts progress metrics from audio pipeline output JSON for frontend visualization:
- Mood Trends: AI-analyzed mood scores over time
- Session Consistency: Attendance patterns and streaks
- (Future) Homework Impact, Strategy Effectiveness

Input: Pipeline JSON with Wave 1 + Wave 2 analysis
Output: Structured metrics ready for frontend charts
"""

from typing import List, Dict, Any, Optional, Literal
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import statistics


# ============================================
# Response Models
# ============================================

class MoodTrendDataPoint(BaseModel):
    """Chart data point for mood trends over time."""
    session: str  # e.g., "S10", "S11"
    mood: float  # 0.0 to 10.0
    date: str  # Display date (e.g., "Dec 23")
    confidence: float = Field(ge=0.0, le=1.0)


class SessionConsistencyDataPoint(BaseModel):
    """Chart data point for weekly attendance."""
    week: str  # e.g., "Week 1"
    attended: int  # 0 or 1 (binary for bar chart)


class ProgressMetric(BaseModel):
    """Single progress metric with chart data."""
    title: str
    description: str
    emoji: str
    insight: str
    chartData: List[Dict[str, Any]]


class ProgressMetricsResponse(BaseModel):
    """Complete progress metrics for frontend visualization."""
    metrics: List[ProgressMetric]
    extracted_at: str
    session_count: int
    date_range: str


# ============================================
# Extraction Logic
# ============================================

class ProgressMetricsExtractor:
    """Extracts progress metrics from pipeline JSON output."""

    @staticmethod
    def extract_from_pipeline_json(pipeline_data: Dict[str, Any]) -> ProgressMetricsResponse:
        """
        Extract all progress metrics from pipeline JSON output.

        Args:
            pipeline_data: Full pipeline JSON with sessions array

        Returns:
            ProgressMetricsResponse with Mood Trends and Session Consistency
        """
        sessions = pipeline_data.get("sessions", [])

        if not sessions:
            raise ValueError("No sessions found in pipeline data")

        # Extract Mood Trends
        mood_metric = ProgressMetricsExtractor._extract_mood_trends(sessions)

        # Extract Session Consistency
        consistency_metric = ProgressMetricsExtractor._extract_session_consistency(sessions)

        # Calculate date range
        session_dates = []
        for session in sessions:
            wave1 = session.get("wave1", {})
            analyzed_at = wave1.get("analyzed_at") or session.get("wave2", {}).get("deep_analysis", {}).get("analyzed_at")
            if analyzed_at:
                session_dates.append(datetime.fromisoformat(analyzed_at.replace("Z", "+00:00")))

        if session_dates:
            min_date = min(session_dates).strftime("%b %d")
            max_date = max(session_dates).strftime("%b %d, %Y")
            date_range = f"{min_date} - {max_date}"
        else:
            date_range = "Unknown"

        return ProgressMetricsResponse(
            metrics=[mood_metric, consistency_metric],
            extracted_at=datetime.utcnow().isoformat() + "Z",
            session_count=len(sessions),
            date_range=date_range,
        )

    @staticmethod
    def _extract_mood_trends(sessions: List[Dict[str, Any]]) -> ProgressMetric:
        """
        Extract mood trend metric from Wave 1 AI analysis.

        Chart data format:
        - session: "S10", "S11", "S12"
        - mood: 5.5, 6.5, 7.5 (0-10 scale)
        - date: "Dec 23", "Dec 24"
        - confidence: 0.85
        """
        chart_data = []
        mood_scores = []

        for session in sessions:
            wave1 = session.get("wave1", {})
            session_num = wave1.get("session_num") or session.get("session_num")
            mood_score = wave1.get("mood_score")
            mood_confidence = wave1.get("mood_confidence", 0.8)
            analyzed_at = wave1.get("analyzed_at") or session.get("wave2", {}).get("deep_analysis", {}).get("analyzed_at")

            if mood_score is not None and session_num is not None:
                # Parse date for display
                if analyzed_at:
                    try:
                        date_obj = datetime.fromisoformat(analyzed_at.replace("Z", "+00:00"))
                        date_str = date_obj.strftime("%b %d")
                    except:
                        date_str = "Unknown"
                else:
                    date_str = "Unknown"

                chart_data.append({
                    "session": f"S{session_num}",
                    "mood": round(mood_score, 1),
                    "date": date_str,
                    "confidence": mood_confidence,
                })
                mood_scores.append(mood_score)

        # Calculate insight
        if len(mood_scores) >= 2:
            first_mood = mood_scores[0]
            last_mood = mood_scores[-1]
            improvement = ((last_mood - first_mood) / first_mood) * 100
            improvement_sign = "+" if improvement > 0 else ""

            # Determine trend direction
            if len(mood_scores) >= 3:
                recent_avg = statistics.mean(mood_scores[-3:])
                historical_avg = statistics.mean(mood_scores[:-3]) if len(mood_scores) > 3 else mood_scores[0]

                if recent_avg > historical_avg + 0.5:
                    direction = "📈 IMPROVING"
                elif recent_avg < historical_avg - 0.5:
                    direction = "📉 DECLINING"
                elif max(mood_scores) - min(mood_scores) > 2.0:
                    direction = "↕️ VARIABLE"
                else:
                    direction = "➡️ STABLE"

                insight = f"{direction}: {improvement_sign}{improvement:.0f}% overall (Recent avg: {recent_avg:.1f}/10, Historical: {historical_avg:.1f}/10)"
            else:
                insight = f"{improvement_sign}{improvement:.0f}% mood change over {len(mood_scores)} sessions"
        else:
            insight = f"Tracking mood across {len(mood_scores)} session(s)"

        return ProgressMetric(
            title="Mood Trends",
            description="AI-analyzed emotional state over time",
            emoji="📈",
            insight=insight,
            chartData=chart_data,
        )

    @staticmethod
    def _extract_session_consistency(sessions: List[Dict[str, Any]]) -> ProgressMetric:
        """
        Extract session consistency metric from session timestamps.

        Chart data format:
        - week: "Week 1", "Week 2"
        - attended: 1 (binary for bar chart)

        Note: Without real session dates, we simulate weekly attendance based on session count.
        In production, this would use actual session.date from database.
        """
        # Simulate weekly attendance (1 session per week for demo)
        # In production, you'd group sessions by week from actual dates
        chart_data = []

        for idx, session in enumerate(sessions, start=1):
            chart_data.append({
                "week": f"Week {idx}",
                "attended": 1,  # Binary: session happened
            })

        # Calculate attendance metrics
        total_weeks = len(sessions)
        attended_weeks = len(sessions)  # All sessions in pipeline are attended
        attendance_rate = (attended_weeks / total_weeks) * 100 if total_weeks > 0 else 0

        # Calculate consistency score (simplified)
        consistency_score = min(100, attendance_rate)  # 100% = perfect consistency

        if consistency_score >= 80:
            score_text = "Excellent"
        elif consistency_score >= 60:
            score_text = "Good"
        else:
            score_text = "Needs improvement"

        insight = f"{attendance_rate:.0f}% attendance rate - {score_text} (Score: {consistency_score:.0f}/100). {total_weeks} week streak."

        return ProgressMetric(
            title="Session Consistency",
            description="Attendance patterns and engagement",
            emoji="📅",
            insight=insight,
            chartData=chart_data,
        )


# ============================================
# Convenience Functions
# ============================================

def extract_progress_metrics(pipeline_json_path: str) -> ProgressMetricsResponse:
    """
    Load pipeline JSON from file and extract progress metrics.

    Args:
        pipeline_json_path: Path to pipeline output JSON file

    Returns:
        ProgressMetricsResponse with all metrics
    """
    import json

    with open(pipeline_json_path, 'r') as f:
        pipeline_data = json.load(f)

    return ProgressMetricsExtractor.extract_from_pipeline_json(pipeline_data)


# ============================================
# Test Script (run directly)
# ============================================

if __name__ == "__main__":
    import sys
    import json

    # Test with demo pipeline output
    demo_json_path = "/Users/newdldewdl/Global Domination 2/peerbridge proj/mock-therapy-data/full_pipeline_demo_20251223_184038.json"

    print("🔍 Extracting Progress Metrics from Pipeline JSON...\n")

    try:
        metrics = extract_progress_metrics(demo_json_path)

        print(f"✅ Extracted {len(metrics.metrics)} metrics")
        print(f"📊 Date Range: {metrics.date_range}")
        print(f"📈 Session Count: {metrics.session_count}\n")

        # Display each metric
        for metric in metrics.metrics:
            print(f"\n{'='*60}")
            print(f"{metric.emoji} {metric.title}")
            print(f"{'='*60}")
            print(f"Description: {metric.description}")
            print(f"Insight: {metric.insight}")
            print(f"\nChart Data ({len(metric.chartData)} points):")
            for point in metric.chartData[:5]:  # Show first 5 points
                print(f"  {point}")
            if len(metric.chartData) > 5:
                print(f"  ... and {len(metric.chartData) - 5} more points")

        # Save output for inspection
        output_path = "progress_metrics_extraction_results.json"
        with open(output_path, 'w') as f:
            json.dump(metrics.model_dump(), f, indent=2)

        print(f"\n\n💾 Full results saved to: {output_path}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
