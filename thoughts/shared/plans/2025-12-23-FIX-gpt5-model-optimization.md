# FIX: GPT-5 Model Optimization Implementation Plan

## Overview

**URGENT FIX**: Replace incorrect model references (o3, o3-mini, gpt-5-mini which DON'T EXIST) with correct GPT-5 series models based on actual December 2025 OpenAI pricing. Implement configuration-driven model selection using ONLY GPT-5 series: gpt-5.2, gpt-5, gpt-5-mini, gpt-5-nano.

## Current State Analysis

### What's Broken

**Current service model references** (ALL WRONG):
1. `mood_analyzer.py:46` - Uses `"gpt-5-mini"` (DOESN'T EXIST - needs `gpt-5-mini`)
2. `topic_extractor.py:49` - Uses `"gpt-5-mini"` (DOESN'T EXIST - needs `gpt-5-mini`)
3. `breakthrough_detector.py:59` - Uses `"gpt-5"` (CORRECT!)
4. `deep_analyzer.py:132` - Uses `"gpt-4o"` (WRONG - needs `gpt-5.2`)

**Previous wrong plan used:**
- o3, o3-mini, o4-mini (NOT GPT-5 series)
- Wrong pricing and context windows
- Temperature constraints that don't apply to GPT-5

### Actual GPT-5 Series Models (December 2025)

Based on your pricing data:

| Model | Input $/1M | Output $/1M | Context | Use Case |
|-------|------------|-------------|---------|----------|
| **gpt-5.2** | $1.75 | $14.00 | 400K | Best for coding/agentic tasks |
| **gpt-5.2-pro** | $21.00 | $168.00 | 400K | Smarter, more precise (premium) |
| **gpt-5** | $1.25 | $10.00 | 400K | Previous reasoning model |
| **gpt-5-mini** | $0.25 | $2.00 | 400K | Fast, cost-efficient |
| **gpt-5-nano** | $0.05 | $0.40 | 400K | Fastest, cheapest |
| **gpt-4.1** | $2.00 | $8.00 | 1,047K | Legacy non-reasoning |

**CRITICAL: GPT-5 series does NOT support custom temperature** - they use internal calibrated randomness (similar to o-series strict behavior). Attempting to set temperature results in API errors.

### Correct Model Selection (Balanced Quality-to-Cost)

| Task | Model | Input | Output | Est. Cost/Session | Rationale |
|------|-------|-------|--------|-------------------|-----------|
| **Mood Analysis** | `gpt-5-nano` | $0.05 | $0.40 | ~$0.001 (0.1¢) | Ultra-cheap, simple scoring |
| **Topic Extraction** | `gpt-5-mini` | $0.25 | $2.00 | ~$0.006 (0.6¢) | Structured extraction, still cheap |
| **Breakthrough Detection** | `gpt-5` | $1.25 | $10.00 | ~$0.028 (2.8¢) | Complex reasoning needed |
| **Deep Analysis** | `gpt-5.2` | $1.75 | $14.00 | ~$0.045 (4.5¢) | Comprehensive synthesis |

**Total per session**: ~**$0.08 (8 cents)**

## Desired End State

**System Configuration:**
```python
TASK_MODEL_ASSIGNMENTS = {
    "mood_analysis": "gpt-5-nano",          # Cheapest for simple scoring
    "topic_extraction": "gpt-5-mini",       # Balance for structured extraction
    "breakthrough_detection": "gpt-5",      # Complex reasoning
    "deep_analysis": "gpt-5.2",             # Best for multi-source synthesis
}
```

**Verification:**
```bash
cd backend
python3 -c "from app.services.mood_analyzer import MoodAnalyzer; a = MoodAnalyzer(); print(f'Mood: {a.model}')"
# Expected: "Mood: gpt-5-nano"

python3 -c "from app.services.topic_extractor import TopicExtractor; t = TopicExtractor(); print(f'Topic: {t.model}')"
# Expected: "Topic: gpt-5-mini"

python3 -c "from app.services.breakthrough_detector import BreakthroughDetector; b = BreakthroughDetector(); print(f'Breakthrough: {b.model}')"
# Expected: "Breakthrough: gpt-5"
```

## What We're NOT Doing

- ❌ NOT using o3, o3-mini, o4-mini (not GPT-5 series)
- ❌ NOT implementing custom temperature (GPT-5 doesn't support it)
- ❌ NOT adding batching or caching (future optimization)
- ❌ NOT changing algorithm logic (only model selection)
- ❌ NOT updating database schema

## Implementation Approach

1. Create configuration module with GPT-5 series models ONLY
2. Update all 4 services to use config (remove hardcoded models)
3. Remove temperature parameters (GPT-5 doesn't support custom values)
4. Test on session_03 to verify all algorithms work
5. Document cost savings (~8¢ per session)

---

## Phase 1: Create GPT-5 Configuration System

### Overview
Build configuration module with ONLY GPT-5 series models and correct pricing.

### Changes Required:

#### 1.1 Create Model Configuration Module

**File**: `backend/app/config/model_config.py` (CREATE NEW)
**Changes**: Create configuration system with GPT-5 models only

```python
"""
GPT-5 Model Configuration System (December 2025)

Centralized model selection for TherapyBridge AI analysis pipeline.
Uses ONLY GPT-5 series models with correct pricing and constraints.

IMPORTANT: GPT-5 models do NOT support custom temperature.
They use internal calibrated randomness - attempting to set temperature
causes API errors.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum


class TaskComplexity(Enum):
    """Complexity levels for AI analysis tasks"""
    ULTRA_LOW = "ultra_low"    # Simple scoring (mood)
    LOW = "low"                # Structured extraction (topics)
    HIGH = "high"              # Complex reasoning (breakthrough)
    VERY_HIGH = "very_high"    # Multi-source synthesis (deep)


@dataclass
class ModelConfig:
    """Configuration for a GPT-5 series model"""
    model_name: str
    cost_per_1m_input: float   # USD
    cost_per_1m_output: float  # USD
    context_window: int        # tokens
    complexity_tier: TaskComplexity
    description: str


# =============================================================================
# GPT-5 Model Registry (December 2025)
# ONLY GPT-5 SERIES MODELS
# =============================================================================

MODEL_REGISTRY = {
    "gpt-5.2": ModelConfig(
        model_name="gpt-5.2",
        cost_per_1m_input=1.75,
        cost_per_1m_output=14.00,
        context_window=400_000,
        complexity_tier=TaskComplexity.VERY_HIGH,
        description="Best model for coding and agentic tasks across industries"
    ),

    "gpt-5.2-pro": ModelConfig(
        model_name="gpt-5.2-pro",
        cost_per_1m_input=21.00,
        cost_per_1m_output=168.00,
        context_window=400_000,
        complexity_tier=TaskComplexity.VERY_HIGH,
        description="Version of GPT-5.2 that produces smarter and more precise responses"
    ),

    "gpt-5": ModelConfig(
        model_name="gpt-5",
        cost_per_1m_input=1.25,
        cost_per_1m_output=10.00,
        context_window=400_000,
        complexity_tier=TaskComplexity.HIGH,
        description="Previous intelligent reasoning model for coding and agentic tasks"
    ),

    "gpt-5-mini": ModelConfig(
        model_name="gpt-5-mini",
        cost_per_1m_input=0.25,
        cost_per_1m_output=2.00,
        context_window=400_000,
        complexity_tier=TaskComplexity.LOW,
        description="Faster, cost-efficient version of GPT-5 for well-defined tasks"
    ),

    "gpt-5-nano": ModelConfig(
        model_name="gpt-5-nano",
        cost_per_1m_input=0.05,
        cost_per_1m_output=0.40,
        context_window=400_000,
        complexity_tier=TaskComplexity.ULTRA_LOW,
        description="Fastest, most cost-efficient version of GPT-5"
    ),

    # Legacy support (not recommended for new tasks)
    "gpt-4.1": ModelConfig(
        model_name="gpt-4.1",
        cost_per_1m_input=2.00,
        cost_per_1m_output=8.00,
        context_window=1_047_576,
        complexity_tier=TaskComplexity.VERY_HIGH,
        description="Smartest non-reasoning model (legacy)"
    ),
}


# =============================================================================
# Task-Specific Model Assignments
# =============================================================================

TASK_MODEL_ASSIGNMENTS = {
    "mood_analysis": "gpt-5-nano",          # Ultra-cheap for simple scoring
    "topic_extraction": "gpt-5-mini",       # Balance for structured extraction
    "breakthrough_detection": "gpt-5",      # Complex reasoning needed
    "deep_analysis": "gpt-5.2",             # Best for comprehensive synthesis
}


# =============================================================================
# Model Selection Functions
# =============================================================================

def get_model_for_task(
    task_name: str,
    override_model: Optional[str] = None
) -> ModelConfig:
    """
    Get model configuration for a specific task.

    Args:
        task_name: Task identifier (e.g., 'mood_analysis')
        override_model: Optional model override (for testing)

    Returns:
        ModelConfig for the selected model

    Raises:
        ValueError: If task or model not found
    """
    # Use override if provided
    if override_model:
        if override_model not in MODEL_REGISTRY:
            raise ValueError(
                f"Unknown model: {override_model}. "
                f"Valid models: {list(MODEL_REGISTRY.keys())}"
            )
        return MODEL_REGISTRY[override_model]

    # Use task-specific assignment
    if task_name not in TASK_MODEL_ASSIGNMENTS:
        raise ValueError(
            f"Unknown task: {task_name}. "
            f"Valid tasks: {list(TASK_MODEL_ASSIGNMENTS.keys())}"
        )

    model_name = TASK_MODEL_ASSIGNMENTS[task_name]
    return MODEL_REGISTRY[model_name]


def get_model_name(
    task_name: str,
    override_model: Optional[str] = None
) -> str:
    """
    Get model name string for OpenAI API calls.

    Args:
        task_name: Task identifier
        override_model: Optional model override

    Returns:
        Model name string (e.g., "gpt-5-nano")
    """
    config = get_model_for_task(task_name, override_model)
    return config.model_name


def estimate_cost(
    task_name: str,
    input_tokens: int,
    output_tokens: int,
    override_model: Optional[str] = None
) -> float:
    """
    Estimate cost for a specific task.

    Args:
        task_name: Task identifier
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        override_model: Optional model override

    Returns:
        Estimated cost in USD

    Example:
        >>> estimate_cost("mood_analysis", 2000, 300)
        0.00022  # $0.00022 = 0.022 cents
    """
    config = get_model_for_task(task_name, override_model)

    input_cost = (input_tokens / 1_000_000) * config.cost_per_1m_input
    output_cost = (output_tokens / 1_000_000) * config.cost_per_1m_output

    return input_cost + output_cost


def get_all_models() -> Dict[str, ModelConfig]:
    """Get all available models in registry"""
    return MODEL_REGISTRY.copy()


def get_task_assignments() -> Dict[str, str]:
    """Get current task-to-model assignments"""
    return TASK_MODEL_ASSIGNMENTS.copy()
```

### Success Criteria:

#### Automated Verification:
- [ ] Config module imports successfully: `python3 -c "from app.config.model_config import get_model_for_task"`
- [ ] All task assignments work: `python3 -c "from app.config.model_config import get_model_for_task; [get_model_for_task(t) for t in ['mood_analysis', 'topic_extraction', 'breakthrough_detection', 'deep_analysis']]"`
- [ ] Cost estimation works: `python3 -c "from app.config.model_config import estimate_cost; print(f'${estimate_cost(\"mood_analysis\", 2000, 300):.6f}')"`

#### Manual Verification:
- [ ] All models in registry are GPT-5 series (no o3, o3-mini, o4-mini)
- [ ] Pricing matches your provided data exactly
- [ ] Context windows are correct (400K for GPT-5 series)

---

## Phase 2: Update Mood Analyzer (gpt-5-mini → gpt-5-nano)

### Overview
Change mood analyzer from non-existent `"gpt-5-mini"` to actual `gpt-5-nano` via config.

### Changes Required:

#### 2.1 Update MoodAnalyzer Class

**File**: `backend/app/services/mood_analyzer.py`
**Changes**: Use config system, remove temperature

```python
# Line 15: Add import
from app.config.model_config import get_model_name

# Lines 46-59: Replace __init__ method
def __init__(self, api_key: Optional[str] = None, override_model: Optional[str] = None):
    """
    Initialize the mood analyzer.

    Args:
        api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
        override_model: Optional model override (for testing). If None, uses gpt-5-nano.
    """
    self.api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not self.api_key:
        raise ValueError("OpenAI API key required for mood analysis")

    openai.api_key = self.api_key

    # Use configuration system
    self.model = get_model_name("mood_analysis", override_model=override_model)

# Lines 92-106: Update API call - REMOVE temperature parameter
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
    ],
    # NO TEMPERATURE - GPT-5 uses internal calibration
    response_format={"type": "json_object"}
)
```

### Success Criteria:

#### Automated Verification:
- [ ] Imports successfully: `python3 -c "from app.services.mood_analyzer import MoodAnalyzer"`
- [ ] Uses gpt-5-nano: `python3 -c "from app.services.mood_analyzer import MoodAnalyzer; a = MoodAnalyzer(); assert a.model == 'gpt-5-nano', f'Expected gpt-5-nano, got {a.model}'"`

#### Manual Verification:
- [ ] No temperature parameter in API call
- [ ] Model comes from config, not hardcoded

---

## Phase 3: Update Topic Extractor (gpt-5-mini → gpt-5-mini)

### Overview
Change topic extractor from non-existent string to actual model via config.

### Changes Required:

#### 3.1 Update TopicExtractor Class

**File**: `backend/app/services/topic_extractor.py`
**Changes**: Use config system, remove temperature

```python
# Line 20: Add import
from app.config.model_config import get_model_name

# Lines 49-65: Replace __init__ method
def __init__(self, api_key: Optional[str] = None, override_model: Optional[str] = None):
    """
    Initialize the topic extractor with technique library.

    Args:
        api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
        override_model: Optional model override (for testing). If None, uses gpt-5-mini.
    """
    self.api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not self.api_key:
        raise ValueError("OpenAI API key required for topic extraction")

    openai.api_key = self.api_key

    # Use configuration system
    self.model = get_model_name("topic_extraction", override_model=override_model)

    # Load technique library for validation
    self.technique_library: TechniqueLibrary = get_technique_library()

# Lines 96-110: Update API call - REMOVE temperature parameter
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
    ],
    # NO TEMPERATURE - GPT-5 uses internal calibration
    response_format={"type": "json_object"}
)
```

### Success Criteria:

#### Automated Verification:
- [ ] Imports successfully: `python3 -c "from app.services.topic_extractor import TopicExtractor"`
- [ ] Uses gpt-5-mini: `python3 -c "from app.services.topic_extractor import TopicExtractor; t = TopicExtractor(); assert t.model == 'gpt-5-mini', f'Expected gpt-5-mini, got {t.model}'"`

#### Manual Verification:
- [ ] No temperature parameter in API call
- [ ] Model comes from config

---

## Phase 4: Update Breakthrough Detector (gpt-5 → gpt-5)

### Overview
Breakthrough detector already uses `gpt-5` correctly! Just need to connect to config system.

### Changes Required:

#### 4.1 Update BreakthroughDetector Class

**File**: `backend/app/services/breakthrough_detector.py`
**Changes**: Use config system (model name already correct!)

```python
# Line 14: Add import
from app.config.model_config import get_model_name

# Lines 53-65: Replace __init__ method
def __init__(self, api_key: Optional[str] = None, override_model: Optional[str] = None):
    """
    Initialize with OpenAI API key and model selection.

    Args:
        api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
        override_model: Optional model override (for testing). If None, uses gpt-5.
    """
    self.api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not self.api_key:
        raise ValueError("OpenAI API key required for breakthrough detection")

    openai.api_key = self.api_key

    # Use configuration system
    self.model = get_model_name("breakthrough_detection", override_model=override_model)

# Lines 166-175: API call already doesn't use temperature - VERIFY NO CHANGES NEEDED
# GPT-5 models handle temperature internally
```

### Success Criteria:

#### Automated Verification:
- [ ] Imports successfully: `python3 -c "from app.services.breakthrough_detector import BreakthroughDetector"`
- [ ] Uses gpt-5: `python3 -c "from app.services.breakthrough_detector import BreakthroughDetector; b = BreakthroughDetector(); assert b.model == 'gpt-5', f'Expected gpt-5, got {b.model}'"`

#### Manual Verification:
- [ ] No temperature parameter in API call
- [ ] Model comes from config

---

## Phase 5: Update Deep Analyzer (gpt-4o → gpt-5.2)

### Overview
Change deep analyzer from outdated `gpt-4o` to `gpt-5.2` via config.

### Changes Required:

#### 5.1 Update DeepAnalyzer Class

**File**: `backend/app/services/deep_analyzer.py`
**Changes**: Use config system, change to gpt-5.2, remove temperature

```python
# Line 24: Add import
from app.config.model_config import get_model_name

# Lines 119-133: Replace __init__ method
def __init__(self, api_key: Optional[str] = None, override_model: Optional[str] = None, db: Optional[Client] = None):
    """
    Initialize the deep analyzer.

    Args:
        api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
        override_model: Optional model override (for testing). If None, uses gpt-5.2.
        db: Supabase client. If None, uses default from get_db()
    """
    self.api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not self.api_key:
        raise ValueError("OpenAI API key required for deep analysis")

    openai.api_key = self.api_key

    # Use configuration system
    self.model = get_model_name("deep_analysis", override_model=override_model)

    self.db = db or next(get_db())

# Lines 159-174: Update API call - REMOVE temperature parameter
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
    ],
    # NO TEMPERATURE - GPT-5 uses internal calibration
    response_format={"type": "json_object"}
)
```

### Success Criteria:

#### Automated Verification:
- [ ] Imports successfully: `python3 -c "from app.services.deep_analyzer import DeepAnalyzer"`
- [ ] Uses gpt-5.2: `python3 -c "from app.services.deep_analyzer import DeepAnalyzer; d = DeepAnalyzer(); assert d.model == 'gpt-5.2', f'Expected gpt-5.2, got {d.model}'"`

#### Manual Verification:
- [ ] No temperature parameter in API call
- [ ] Model comes from config

---

## Phase 6: Verification & Cost Analysis

### Overview
Run all algorithms on session_03 to verify GPT-5 models work correctly and calculate actual costs.

### Success Criteria:

#### Automated Verification:
- [ ] All services import: `python3 -c "from app.services.mood_analyzer import MoodAnalyzer; from app.services.topic_extractor import TopicExtractor; from app.services.breakthrough_detector import BreakthroughDetector; from app.services.deep_analyzer import DeepAnalyzer; print('All imports successful')"`
- [ ] Model assignments correct:
  ```bash
  python3 -c "
  from app.services.mood_analyzer import MoodAnalyzer
  from app.services.topic_extractor import TopicExtractor
  from app.services.breakthrough_detector import BreakthroughDetector
  from app.services.deep_analyzer import DeepAnalyzer

  a = MoodAnalyzer()
  t = TopicExtractor()
  b = BreakthroughDetector()
  d = DeepAnalyzer()

  print(f'Mood: {a.model} (expected: gpt-5-nano)')
  print(f'Topic: {t.model} (expected: gpt-5-mini)')
  print(f'Breakthrough: {b.model} (expected: gpt-5)')
  print(f'Deep: {d.model} (expected: gpt-5.2)')

  assert a.model == 'gpt-5-nano'
  assert t.model == 'gpt-5-mini'
  assert b.model == 'gpt-5'
  assert d.model == 'gpt-5.2'
  print('✓ All models correct!')
  "
  ```

#### Manual Verification:
- [ ] Run demo script on session_03 (if API key available)
- [ ] Verify all algorithms complete successfully
- [ ] Calculate actual cost per session (~8¢ expected)
- [ ] Compare to old cost (should be significant savings)

---

## Cost Comparison

### Before (Wrong Models - Would Fail Anyway)
- Models don't exist, would get 404 errors
- N/A

### After (Correct GPT-5 Models)

| Task | Model | Est. Tokens | Est. Cost |
|------|-------|-------------|-----------|
| Mood Analysis | gpt-5-nano | 2K in, 300 out | $0.00022 (0.02¢) |
| Topic Extraction | gpt-5-mini | 2K in, 300 out | $0.00110 (0.11¢) |
| Breakthrough Detection | gpt-5 | 2K in, 400 out | $0.00650 (0.65¢) |
| Deep Analysis | gpt-5.2 | 5K in, 800 out | $0.01995 (2.00¢) |
| **TOTAL** | - | - | **~$0.028 (2.8¢)** |

**Note**: Deep analysis only runs if Wave 1 triggers it. Wave 1 alone costs ~**0.78¢ per session**.

---

## References

- **Your Pricing Data**: GPT-5 series pricing from your message
- **OpenAI Pricing Page**: https://platform.openai.com/docs/pricing
- **GPT-5 Models Page**: https://platform.openai.com/docs/models
- **Current Services**: `backend/app/services/*.py`
- **Demo Output**: `mock-therapy-data/session_03_alex_chen_all_algorithms_output.json`

---

**Implementation Time**: ~2-3 hours
**Complexity**: LOW (config + 4 simple updates)
**Risk**: LOW (config-driven, easy to test/rollback)
