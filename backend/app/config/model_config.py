"""
Model Configuration for AI Analysis Services

Centralized configuration for OpenAI GPT-5 series model selection.
Maps each analysis task to the optimal GPT-5 model based on complexity and cost.

NOTE: GPT-5 series models do NOT support custom temperature parameters.
They use internal calibrated randomness - attempting to set temperature causes API errors.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


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


# Task-Based Model Assignments
# Each analysis task is mapped to the optimal GPT-5 model
TASK_MODEL_ASSIGNMENTS = {
    "mood_analysis": "gpt-5-nano",          # Simple 0-10 scoring with rationale
    "topic_extraction": "gpt-5-mini",       # Structured metadata extraction
    "action_summary": "gpt-4o-mini",        # TEMP FIX: Use gpt-4o-mini (GPT-5-nano returns empty)
    "breakthrough_detection": "gpt-5",      # Complex clinical reasoning required
    "deep_analysis": "gpt-5.2",             # Comprehensive synthesis of all data
    "prose_generation": "gpt-5.2",          # Patient-facing prose narrative
    "speaker_labeling": "gpt-5-mini",       # Speaker role detection + formatting
}


# Cost Estimation (based on typical session processing)
ESTIMATED_TOKEN_USAGE = {
    "mood_analysis": {"input": 2000, "output": 200},       # ~$0.0005 per session
    "topic_extraction": {"input": 3000, "output": 300},    # ~$0.0013 per session
    "breakthrough_detection": {"input": 3500, "output": 400}, # ~$0.0084 per session
    "deep_analysis": {"input": 5000, "output": 800},       # ~$0.0200 per session
    "prose_generation": {"input": 2000, "output": 600},    # ~$0.0118 per session
    "speaker_labeling": {"input": 2500, "output": 150},    # ~$0.0009 per session
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


if __name__ == "__main__":
    # Print configuration summary when run directly
    print_model_summary()
