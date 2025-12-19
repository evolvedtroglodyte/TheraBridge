import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from dotenv import load_dotenv

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Load environment variables
load_dotenv()

# Import Base and all models for autogenerate support
from app.database import Base

# Import auth models (User, AuthSession for authentication)
from app.auth.models import User, AuthSession

# Import core session and patient models from db_models
from app.models.db_models import (
    TherapySession,
    Patient,
    TherapistPatient,
    TimelineEvent,
    NoteTemplate,
    SessionNote,
    TemplateUsage
)

# Import analytics models for Feature 2
from app.models.analytics_models import SessionMetrics, DailyStats, PatientProgress

# Import goal tracking models for Feature 6
from app.models.goal_models import TreatmentGoal
from app.models.tracking_models import (
    GoalTrackingConfig,
    ProgressEntry,
    AssessmentScore,
    ProgressMilestone,
    GoalReminder
)

# Import treatment plan models for Feature 4
from app.models.treatment_models import (
    TreatmentPlan,
    TreatmentPlanGoal,
    Intervention,
    GoalIntervention,
    GoalProgress,
    PlanReview
)

# Import security and compliance models for HIPAA compliance
from app.models.security_models import (
    AuditLog,
    SecurityEvent,
    MFAConfig,
    UserSession,
    AccessRequest,
    EmergencyAccess,
    ConsentRecord,
    EncryptionKey
)

# Import export and reporting models for Feature 7
from app.models.export_models import (
    ExportTemplate,
    ExportJob,
    ExportAuditLog,
    ScheduledReport
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Get database URL from environment and convert to sync version for Alembic
database_url = os.getenv("DATABASE_URL")
if database_url:
    # Convert async URL to sync URL for Alembic
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    # Set in config for Alembic to use
    config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target_metadata to Base.metadata for autogenerate support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
