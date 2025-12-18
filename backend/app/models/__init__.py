"""
Models package

IMPORTANT: All model files must be imported here to register with Base.metadata
This ensures tables are created when Base.metadata.create_all() is called in tests
"""

# Import all model modules to register tables with Base.metadata
# Do not remove these imports even if they appear unused!
import app.models.db_models  # Core models: User, Patient, Session, etc.
import app.models.analytics_models  # Analytics tables
import app.models.export_models  # Export and reporting tables
import app.models.security_models  # Security and compliance tables
import app.models.goal_models  # Treatment goals (includes TreatmentGoal)
import app.models.tracking_models  # Goal tracking, progress, assessments
import app.models.treatment_models  # Treatment plans and interventions
import app.auth.models  # AuthSession

# Goal tracking models (Feature 6)
from app.models.goal_models import TreatmentGoal
from app.models.tracking_models import (
    GoalTrackingConfig,
    ProgressEntry,
    AssessmentScore,
    ProgressMilestone,
    GoalReminder
)

from app.models.treatment_models import (
    TreatmentPlan,
    TreatmentPlanGoal,
    Intervention,
    GoalIntervention,
    GoalProgress,
    PlanReview
)

__all__ = [
    "TreatmentGoal",
    "GoalTrackingConfig",
    "ProgressEntry",
    "AssessmentScore",
    "ProgressMilestone",
    "GoalReminder",
    "TreatmentPlan",
    "TreatmentPlanGoal",
    "Intervention",
    "GoalIntervention",
    "GoalProgress",
    "PlanReview",
]
