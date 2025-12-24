"""
Model Configuration for AI Analysis Services

Centralized configuration for OpenAI GPT-5 series model selection.
Maps each analysis task to the optimal GPT-5 model based on complexity and cost.

Supports MODEL_TIER system for cost optimization:
- precision: Highest quality (gpt-5.2 for complex tasks) - baseline cost
- balanced: Good quality (gpt-5 for most tasks) - 72% cost savings
- rapid: Development/testing mode (gpt-5-mini for all) - 94% cost savings

NOTE: GPT-5 series models do NOT support custom temperature parameters.
They use internal calibrated randomness - attempting to set temperature causes API errors.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any, Literal
from datetime import datetime
import time
import logging
import os

logger = logging.getLogger(__name__)


# =============================================================================
# MODEL_TIER System
# =============================================================================

class ModelTier(str, Enum):
    """
    Model tier for cost vs quality tradeoffs.

    - PRECISION: Highest quality, uses configured models (gpt-5.2 for complex tasks)
    - BALANCED: Good quality at 72% cost savings (gpt-5 for most tasks)
    - RAPID: Fast development/testing mode at 94% savings (gpt-5-mini for all)
    """
    PRECISION = "precision"
    BALANCED = "balanced"
    RAPID = "rapid"


# Tier-based model assignments
# Maps each tier to the models used for each task
TIER_ASSIGNMENTS = {
    ModelTier.PRECISION: {
        # Uses the original task-optimal models
        "mood_analysis": "gpt-5-nano",
        "topic_extraction": "gpt-5-mini",
        "action_summary": "gpt-5-nano",
        "breakthrough_detection": "gpt-5",
        "deep_analysis": "gpt-5.2",
        "prose_generation": "gpt-5.2",
        "speaker_labeling": "gpt-5-mini",
        "session_insights": "gpt-5.2",
        "roadmap_generation": "gpt-5.2",
        "session_bridge_generation": "gpt-5.2",  # New task
    },
    ModelTier.BALANCED: {
        # Downgrades expensive models to gpt-5 for 72% savings
        "mood_analysis": "gpt-5-nano",
        "topic_extraction": "gpt-5-mini",
        "action_summary": "gpt-5-nano",
        "breakthrough_detection": "gpt-5-mini",  # Downgraded from gpt-5
        "deep_analysis": "gpt-5",                # Downgraded from gpt-5.2
        "prose_generation": "gpt-5",             # Downgraded from gpt-5.2
        "speaker_labeling": "gpt-5-mini",
        "session_insights": "gpt-5",             # Downgraded from gpt-5.2
        "roadmap_generation": "gpt-5",           # Downgraded from gpt-5.2
        "session_bridge_generation": "gpt-5",    # Downgraded from gpt-5.2
    },
    ModelTier.RAPID: {
        # Uses gpt-5-mini for all tasks for 94% savings
        "mood_analysis": "gpt-5-nano",
        "topic_extraction": "gpt-5-mini",
        "action_summary": "gpt-5-nano",
        "breakthrough_detection": "gpt-5-mini",
        "deep_analysis": "gpt-5-mini",
        "prose_generation": "gpt-5-mini",
        "speaker_labeling": "gpt-5-mini",
        "session_insights": "gpt-5-mini",
        "roadmap_generation": "gpt-5-mini",
        "session_bridge_generation": "gpt-5-mini",
    },
}


# Module-level cache for current tier (lazy loaded from environment)
_cached_tier: Optional[ModelTier] = None


def get_current_tier() -> ModelTier:
    """
    Get the currently active model tier.

    Reads from MODEL_TIER environment variable, defaults to PRECISION.
    Result is cached for performance.

    Returns:
        ModelTier enum value

    Examples:
        >>> os.environ["MODEL_TIER"] = "balanced"
        >>> get_current_tier()
        ModelTier.BALANCED
    """
    global _cached_tier

    if _cached_tier is not None:
        return _cached_tier

    tier_str = os.getenv("MODEL_TIER", "precision").lower()

    try:
        _cached_tier = ModelTier(tier_str)
    except ValueError:
        logger.warning(f"Invalid MODEL_TIER '{tier_str}', defaulting to precision")
        _cached_tier = ModelTier.PRECISION

    logger.info(f"Model tier initialized: {_cached_tier.value}")
    return _cached_tier


def set_tier(tier: ModelTier) -> None:
    """
    Set the current model tier programmatically.

    Useful for testing or runtime tier switching.

    Args:
        tier: ModelTier to set
    """
    global _cached_tier
    _cached_tier = tier
    logger.info(f"Model tier set to: {tier.value}")


def reset_tier_cache() -> None:
    """Reset the tier cache to re-read from environment."""
    global _cached_tier
    _cached_tier = None


class TaskComplexity(Enum):
    """Task complexity levels for model selection"""
    VERY_LOW = "very_low"      # Simple scoring/classification
    LOW = "low"                # Basic extraction
    MEDIUM = "medium"          # Structured extraction
    HIGH = "high"              # Complex reasoning
    VERY_HIGH = "very_high"    # Advanced synthesis


@dataclass
class ModelConfig:
    """Configuration for a specific OpenAI model"""
    model_name: str
    cost_per_1m_input: float   # Cost per 1M input tokens (USD)
    cost_per_1m_output: float  # Cost per 1M output tokens (USD)
    context_window: int        # Maximum context window size
    complexity_tier: TaskComplexity
    description: str


# GPT-5 Series Model Registry
# All models have 400K context windows
# Pricing as of December 2025
MODEL_REGISTRY = {
    "gpt-5.2": ModelConfig(
        model_name="gpt-5.2",
        cost_per_1m_input=1.75,
        cost_per_1m_output=14.00,
        context_window=400_000,
        complexity_tier=TaskComplexity.VERY_HIGH,
        description="Best model for coding and agentic tasks requiring deep synthesis"
    ),
    "gpt-5": ModelConfig(
        model_name="gpt-5",
        cost_per_1m_input=1.25,
        cost_per_1m_output=10.00,
        context_window=400_000,
        complexity_tier=TaskComplexity.HIGH,
        description="Strong reasoning model for complex therapeutic analysis"
    ),
    "gpt-5-mini": ModelConfig(
        model_name="gpt-5-mini",
        cost_per_1m_input=0.25,
        cost_per_1m_output=2.00,
        context_window=400_000,
        complexity_tier=TaskComplexity.MEDIUM,
        description="Cost-efficient for well-defined structured extraction tasks"
    ),
    "gpt-5-nano": ModelConfig(
        model_name="gpt-5-nano",
        cost_per_1m_input=0.05,
        cost_per_1m_output=0.40,
        context_window=400_000,
        complexity_tier=TaskComplexity.VERY_LOW,
        description="Fastest, most cost-efficient for simple classification/scoring"
    ),
    "gpt-5.2-pro": ModelConfig(
        model_name="gpt-5.2-pro",
        cost_per_1m_input=21.00,
        cost_per_1m_output=168.00,
        context_window=400_000,
        complexity_tier=TaskComplexity.VERY_HIGH,
        description="Premium model for maximum precision (typically not needed)"
    ),
}


# Task-Based Model Assignments (Default - PRECISION tier)
# Each analysis task is mapped to the optimal GPT-5 model
# NOTE: These are the defaults; actual model selection respects MODEL_TIER
TASK_MODEL_ASSIGNMENTS = {
    "mood_analysis": "gpt-5-nano",          # Simple 0-10 scoring with rationale
    "topic_extraction": "gpt-5-mini",       # Structured metadata extraction
    "action_summary": "gpt-5-nano",         # Condense action items to 45 chars
    "breakthrough_detection": "gpt-5",      # Complex clinical reasoning required
    "deep_analysis": "gpt-5.2",             # Comprehensive synthesis of all data
    "prose_generation": "gpt-5.2",          # Patient-facing prose narrative
    "speaker_labeling": "gpt-5-mini",       # Speaker role detection + formatting
    "session_insights": "gpt-5.2",          # Extract key insights from deep_analysis
    "roadmap_generation": "gpt-5.2",        # Generate patient journey roadmap
    "session_bridge_generation": "gpt-5.2", # Generate session bridge for patient sharing
}


# Cost Estimation (based on typical session processing)
ESTIMATED_TOKEN_USAGE = {
    "mood_analysis": {"input": 2000, "output": 200},       # ~$0.0005 per session
    "topic_extraction": {"input": 3000, "output": 300},    # ~$0.0013 per session
    "breakthrough_detection": {"input": 3500, "output": 400}, # ~$0.0084 per session
    "deep_analysis": {"input": 5000, "output": 800},       # ~$0.0200 per session
    "prose_generation": {"input": 2000, "output": 600},    # ~$0.0118 per session
    "speaker_labeling": {"input": 2500, "output": 150},    # ~$0.0009 per session
    "session_insights": {"input": 1500, "output": 150},    # ~$0.0006 per session
    "roadmap_generation": {"input": 10000, "output": 1000},  # ~$0.003-0.020 per generation (varies by strategy)
}


def get_model_name(task: str, override_model: Optional[str] = None) -> str:
    """
    Get the configured model name for a specific task.

    Args:
        task: Task identifier (e.g., "mood_analysis", "topic_extraction")
        override_model: Optional model override for testing/experimentation

    Returns:
        Model name string (e.g., "gpt-5-nano")

    Raises:
        ValueError: If task is not recognized or override_model is invalid

    Examples:
        >>> get_model_name("mood_analysis")
        'gpt-5-nano'

        >>> get_model_name("deep_analysis", override_model="gpt-5.2-pro")
        'gpt-5.2-pro'
    """
    if override_model:
        if override_model not in MODEL_REGISTRY:
            valid_models = ", ".join(MODEL_REGISTRY.keys())
            raise ValueError(
                f"Invalid override model '{override_model}'. "
                f"Must be one of: {valid_models}"
            )
        return override_model

    if task not in TASK_MODEL_ASSIGNMENTS:
        valid_tasks = ", ".join(TASK_MODEL_ASSIGNMENTS.keys())
        raise ValueError(
            f"Unknown task '{task}'. "
            f"Must be one of: {valid_tasks}"
        )

    # Apply MODEL_TIER overrides if tier is not precision
    current_tier = get_current_tier()
    if current_tier in TIER_ASSIGNMENTS and task in TIER_ASSIGNMENTS[current_tier]:
        return TIER_ASSIGNMENTS[current_tier][task]

    # Fallback to default assignment
    return TASK_MODEL_ASSIGNMENTS[task]


def get_model_config(model_name: str) -> ModelConfig:
    """
    Get the full configuration for a specific model.

    Args:
        model_name: Name of the model (e.g., "gpt-5-nano")

    Returns:
        ModelConfig object with pricing and metadata

    Raises:
        ValueError: If model_name is not recognized
    """
    if model_name not in MODEL_REGISTRY:
        valid_models = ", ".join(MODEL_REGISTRY.keys())
        raise ValueError(
            f"Unknown model '{model_name}'. "
            f"Must be one of: {valid_models}"
        )

    return MODEL_REGISTRY[model_name]


def estimate_task_cost(task: str, override_model: Optional[str] = None) -> float:
    """
    Estimate the cost (in USD) for running a specific task.

    Args:
        task: Task identifier
        override_model: Optional model override

    Returns:
        Estimated cost in USD per execution

    Examples:
        >>> estimate_task_cost("mood_analysis")
        0.0005  # ~$0.0005 per session
    """
    model_name = get_model_name(task, override_model=override_model)
    model_config = get_model_config(model_name)

    if task not in ESTIMATED_TOKEN_USAGE:
        return 0.0  # Unknown task, can't estimate

    usage = ESTIMATED_TOKEN_USAGE[task]
    input_cost = (usage["input"] / 1_000_000) * model_config.cost_per_1m_input
    output_cost = (usage["output"] / 1_000_000) * model_config.cost_per_1m_output

    return input_cost + output_cost


def get_all_tasks() -> list[str]:
    """Get list of all configured tasks."""
    return list(TASK_MODEL_ASSIGNMENTS.keys())


def get_all_models() -> list[str]:
    """Get list of all available GPT-5 models."""
    return list(MODEL_REGISTRY.keys())


# Summary Statistics
def print_model_summary() -> None:
    """Print a summary of model assignments and estimated costs."""
    print("\n=== GPT-5 Model Configuration Summary ===\n")

    total_cost = 0.0

    for task, model_name in TASK_MODEL_ASSIGNMENTS.items():
        config = get_model_config(model_name)
        cost = estimate_task_cost(task)
        total_cost += cost

        print(f"{task.upper().replace('_', ' ')}")
        print(f"  Model: {model_name}")
        print(f"  Tier: {config.complexity_tier.value}")
        print(f"  Cost: ${cost:.4f} per session")
        print()

    print(f"TOTAL ESTIMATED COST: ${total_cost:.4f} per session (~{total_cost * 100:.2f}¢)")
    print("\n" + "=" * 50 + "\n")


@dataclass
class GenerationCost:
    """
    Tracks cost and timing for a single AI generation.

    Attributes:
        task: The task type (e.g., "deep_analysis", "mood_analysis")
        model: The model used (e.g., "gpt-5.2", "gpt-5-nano")
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        cost: Total cost in USD
        duration_ms: Generation time in milliseconds
        timestamp: When the generation occurred
        session_id: Optional session ID for tracking
        metadata: Optional additional metadata
    """
    task: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    duration_ms: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization or database storage."""
        return {
            "task": self.task,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost": self.cost,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "metadata": self.metadata
        }


def calculate_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate the actual cost for a generation based on token usage.

    Args:
        model_name: Name of the model used (e.g., "gpt-5.2")
        input_tokens: Number of input tokens used
        output_tokens: Number of output tokens generated

    Returns:
        Cost in USD

    Example:
        >>> calculate_cost("gpt-5.2", 5000, 800)
        0.0199  # $0.0199
    """
    if model_name not in MODEL_REGISTRY:
        logger.warning(f"Unknown model '{model_name}' for cost calculation, returning 0")
        return 0.0

    config = MODEL_REGISTRY[model_name]
    input_cost = (input_tokens / 1_000_000) * config.cost_per_1m_input
    output_cost = (output_tokens / 1_000_000) * config.cost_per_1m_output

    return input_cost + output_cost


def store_generation_cost_sync(
    cost_info: 'GenerationCost',
    patient_id: Optional[str] = None
) -> None:
    """
    Synchronous version of store_generation_cost for non-async contexts.

    Uses a direct database connection without async/await.

    Args:
        cost_info: GenerationCost object from track_generation_cost()
        patient_id: Optional patient UUID string for association
    """
    import os
    import psycopg2
    import json

    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            logger.warning("DATABASE_URL not set, skipping cost storage")
            return

        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO generation_costs (
                task, model, input_tokens, output_tokens, cost, duration_ms,
                session_id, patient_id, metadata, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                cost_info.task,
                cost_info.model,
                cost_info.input_tokens,
                cost_info.output_tokens,
                cost_info.cost,
                cost_info.duration_ms,
                cost_info.session_id,
                patient_id,
                json.dumps(cost_info.metadata) if cost_info.metadata else None,
                cost_info.timestamp
            )
        )
        conn.commit()
        cur.close()
        conn.close()
        logger.debug(f"Stored generation cost: {cost_info.task} = ${cost_info.cost:.6f}")
    except Exception as e:
        logger.error(f"Failed to store generation cost (sync): {e}")
        # Don't raise - cost tracking failure shouldn't break the main flow


def track_generation_cost(
    response: Any,
    task: str,
    model: str,
    start_time: float,
    session_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    metadata: Optional[dict] = None,
    persist: bool = True
) -> GenerationCost:
    """
    Extract cost information from an OpenAI API response and create a GenerationCost record.
    Automatically persists to database by default.

    Args:
        response: The OpenAI API response object (ChatCompletion)
        task: Task identifier (e.g., "deep_analysis", "mood_analysis")
        model: Model name used (e.g., "gpt-5.2")
        start_time: time.time() value from before the API call
        session_id: Optional session ID for tracking
        patient_id: Optional patient ID for tracking
        metadata: Optional additional metadata to store
        persist: Whether to store in database (default: True)

    Returns:
        GenerationCost object with all tracking information

    Example:
        start = time.time()
        response = client.chat.completions.create(...)
        cost_info = track_generation_cost(response, "deep_analysis", "gpt-5.2", start, session_id)
    """
    end_time = time.time()
    duration_ms = int((end_time - start_time) * 1000)

    # Extract token usage from response
    input_tokens = response.usage.prompt_tokens if response.usage else 0
    output_tokens = response.usage.completion_tokens if response.usage else 0

    # Calculate actual cost
    cost = calculate_cost(model, input_tokens, output_tokens)

    generation_cost = GenerationCost(
        task=task,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost=cost,
        duration_ms=duration_ms,
        session_id=session_id,
        metadata=metadata
    )

    # Log for visibility
    logger.info(
        f"[Cost] {task}: {input_tokens} in / {output_tokens} out = ${cost:.6f} ({duration_ms}ms)"
    )
    print(
        f"[Cost] {task}: {input_tokens} in / {output_tokens} out = ${cost:.6f} ({duration_ms}ms)",
        flush=True
    )

    # Persist to database (sync, non-blocking failure)
    if persist:
        store_generation_cost_sync(generation_cost, patient_id=patient_id)

    return generation_cost


async def store_generation_cost(
    cost_info: GenerationCost,
    patient_id: Optional[str] = None
) -> None:
    """
    Store a GenerationCost record in the database.

    This function is async because database operations should be non-blocking.
    Call this after track_generation_cost() to persist the cost data.

    Args:
        cost_info: GenerationCost object from track_generation_cost()
        patient_id: Optional patient UUID string for association

    Example:
        cost_info = track_generation_cost(response, "deep_analysis", "gpt-5.2", start, session_id)
        await store_generation_cost(cost_info, patient_id=str(patient.id))
    """
    # Import here to avoid circular imports
    from app.database import get_db_connection

    try:
        conn = await get_db_connection()
        await conn.execute(
            """
            INSERT INTO generation_costs (
                task, model, input_tokens, output_tokens, cost, duration_ms,
                session_id, patient_id, metadata, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            cost_info.task,
            cost_info.model,
            cost_info.input_tokens,
            cost_info.output_tokens,
            cost_info.cost,
            cost_info.duration_ms,
            cost_info.session_id,  # Can be None
            patient_id,  # Can be None
            cost_info.metadata,  # JSONB, can be None
            cost_info.timestamp
        )
        await conn.close()
    except Exception as e:
        logger.error(f"Failed to store generation cost: {e}")
        # Don't raise - cost tracking failure shouldn't break the main flow


if __name__ == "__main__":
    # Print configuration summary when run directly
    print_model_summary()
