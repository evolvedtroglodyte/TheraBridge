# OpenAI Model Optimization & Dynamic Model Selection Implementation Plan

## Overview

Upgrade the TherapyBridge AI analysis pipeline to use the latest OpenAI models (December 2025) with dynamic model selection based on task complexity and cost efficiency. This plan addresses current failures (hardcoded "gpt-5-mini" and "gpt-5" don't exist) and implements a flexible configuration system for optimal model selection.

## Current State Analysis

### Existing Algorithm Architecture

**4 Core AI Services** (all in `backend/app/services/`):

1. **Mood Analysis** (`mood_analyzer.py`) - Analyzes patient emotional state (0-10 scale)
   - Current model: `gpt-5-mini` (hardcoded, DOES NOT EXIST)
   - Temperature: 0.3 (fails with o-series models)
   - Cost: ~$0.01 per session
   - Complexity: LOW (single-dimension scoring)

2. **Topic Extraction** (`topic_extractor.py`) - Extracts topics, action items, technique, summary
   - Current model: `gpt-5-mini` (hardcoded, DOES NOT EXIST)
   - Temperature: 0.3 (fails with o-series models)
   - Cost: ~$0.01 per session
   - Complexity: MEDIUM (structured extraction with validation)

3. **Breakthrough Detection** (`breakthrough_detector.py`) - Identifies major therapeutic insights
   - Current model: `gpt-5` (hardcoded, DOES NOT EXIST)
   - Temperature: 0.3 (fails with o-series models)
   - Cost: ~$0.05 per session (estimated)
   - Complexity: HIGH (complex reasoning, pattern recognition)
   - **NOTE**: Already working with o-series models (likely fallback mechanism)

4. **Deep Analysis** (`deep_analyzer.py`) - Comprehensive clinical synthesis
   - Current model: `gpt-4o` (hardcoded, EXISTS but suboptimal)
   - Temperature: 0.3
   - Cost: ~$0.15 per session (estimated)
   - Complexity: VERY HIGH (synthesizes all Wave 1 + patient history)

**Orchestration System** (`analysis_orchestrator.py`):
- Manages 2-wave pipeline:
  - **Wave 1** (parallel): Mood, Topics, Breakthrough
  - **Wave 2** (sequential): Deep Analysis (requires Wave 1)
- Retry logic, timeout handling, status tracking

### Key Discoveries

**Current Failures:**
- `mood_analyzer.py:46` - Model "gpt-5-mini" does not exist ❌
- `topic_extractor.py:49` - Model "gpt-5-mini" does not exist ❌
- `breakthrough_detector.py:53` - Model "gpt-5" does not exist (but works somehow?)
- `deep_analyzer.py:132` - Model "gpt-4o" exists but outdated ✓

**Temperature Constraint Discovery:**
- o-series models (o3, o4-mini) only support `temperature=1.0` (default)
- Attempting `temperature=0.3` returns 400 error
- GPT-4o-mini and GPT-4.1 mini support custom temperature values

**Current Test Results** (`session_03_all_algorithms_output.json`):
- Mood Analysis: ❌ FAILED (unsupported temperature)
- Topic Extraction: ❌ FAILED (unsupported temperature)
- Breakthrough Detection: ✅ SUCCESS (found ADHD discovery breakthrough, confidence 0.95)
- Technique Validation: ❌ FAILED (cascading error from topic extraction)

### Latest OpenAI Models (December 2025)

Based on web research as of December 2025:

**o-series (Reasoning Models)**:
- `o3` - Most capable reasoning model
  - Input: $10/1M tokens, Output: $40/1M tokens
  - Temperature: **1.0 only** (no customization)
  - Context: 200K tokens
  - Best for: Complex reasoning, coding, science
  - **Use case**: Deep Analysis (highest complexity)

- `o3-mini` - Smaller reasoning model
  - Input: $1.10/1M tokens, Output: $4.40/1M tokens
  - `o3-mini-flex` (slower): Input $0.55/1M, Output $2.20/1M
  - Temperature: **1.0 only** (no customization)
  - Context: 200K tokens
  - **Use case**: Breakthrough Detection (high complexity, cost-sensitive)

- `o4-mini` - Latest compact reasoning model
  - Input: ~$0.55/1M tokens (estimated), Output: ~$2.20/1M tokens (estimated)
  - Temperature: **1.0 only** (no customization)
  - Context: 200K tokens
  - Best for: Math, coding, visual tasks
  - **Use case**: Potential alternative to o3-mini

**GPT-4 Series (General Purpose)**:
- `gpt-4.1` - Latest GPT-4 iteration
  - Pricing: TBD (likely similar to GPT-4o)
  - Temperature: Fully customizable
  - **Status**: Being rolled out, may not be widely available yet

- `gpt-4o` - Latest stable GPT-4 optimized model
  - Input: $5/1M tokens, Output: $15/1M tokens
  - Temperature: Fully customizable
  - **Use case**: Fallback for deep analysis if o3 too expensive

- `gpt-4o-mini` - Most cost-efficient GPT-4 variant
  - Input: **$0.15/1M tokens**, Output: **$0.60/1M tokens**
  - Temperature: Fully customizable (0.0-2.0)
  - 60% cheaper than GPT-3.5 Turbo
  - **Use case**: Mood Analysis, Topic Extraction (low-medium complexity, cost-optimized)

**GPT-4.1 Mini**:
- `gpt-4.1-mini` - Latest mini variant
  - Pricing: Similar to GPT-4o-mini (~$0.15/1M input)
  - Temperature: Fully customizable
  - **Use case**: Alternative to gpt-4o-mini

## Desired End State

### Model Selection Strategy (Balanced Quality-to-Cost)

**Tier 1: Ultra Low-Cost (Simple Tasks)**
- Model: `gpt-4o-mini`
- Temperature: 0.3 (consistency)
- Cost: $0.15 input / $0.60 output per 1M tokens
- Use for:
  - **Mood Analysis** ✅
  - **Topic Extraction** ✅

**Tier 2: Low-Cost Reasoning (Medium Complexity)**
- Model: `o3-mini-flex` (slower but 50% cheaper)
- Temperature: 1.0 (required)
- Cost: $0.55 input / $2.20 output per 1M tokens
- Use for:
  - **Breakthrough Detection** ✅

**Tier 3: High-Performance Reasoning (Complex Synthesis)**
- Model: `o3`
- Temperature: 1.0 (required)
- Cost: $10 input / $40 output per 1M tokens
- Use for:
  - **Deep Analysis** ✅

### Configuration System Architecture

**New File**: `backend/app/config/model_config.py`

```python
"""
OpenAI Model Configuration System

Provides centralized model selection, temperature management,
and cost optimization for AI analysis pipeline.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum


class TaskComplexity(Enum):
    """Complexity levels for AI analysis tasks"""
    LOW = "low"           # Simple scoring, classification
    MEDIUM = "medium"     # Structured extraction, pattern detection
    HIGH = "high"         # Complex reasoning, breakthrough detection
    VERY_HIGH = "very_high"  # Multi-source synthesis, clinical reasoning


class CostTier(Enum):
    """Cost optimization tiers"""
    ULTRA_LOW = "ultra_low"   # GPT-4o-mini tier (~$0.15/1M)
    LOW = "low"               # o3-mini-flex tier (~$0.55/1M)
    MEDIUM = "medium"         # o3-mini tier (~$1.10/1M)
    HIGH = "high"             # o3 tier (~$10/1M)


@dataclass
class ModelConfig:
    """Configuration for a specific OpenAI model"""
    model_name: str
    supports_temperature: bool
    default_temperature: float
    cost_per_1m_input: float  # USD
    cost_per_1m_output: float  # USD
    max_context: int  # tokens
    complexity_tier: TaskComplexity
    cost_tier: CostTier
    description: str


# =============================================================================
# Model Registry (December 2025)
# =============================================================================

MODEL_REGISTRY = {
    # GPT-4o Mini - Ultra low-cost general purpose
    "gpt-4o-mini": ModelConfig(
        model_name="gpt-4o-mini",
        supports_temperature=True,
        default_temperature=0.3,
        cost_per_1m_input=0.15,
        cost_per_1m_output=0.60,
        max_context=128_000,
        complexity_tier=TaskComplexity.LOW,
        cost_tier=CostTier.ULTRA_LOW,
        description="Most cost-efficient GPT-4 model, 60% cheaper than GPT-3.5"
    ),

    # o3-mini-flex - Low-cost reasoning (slower)
    "o3-mini-flex": ModelConfig(
        model_name="o3-mini-flex",
        supports_temperature=False,
        default_temperature=1.0,
        cost_per_1m_input=0.55,
        cost_per_1m_output=2.20,
        max_context=200_000,
        complexity_tier=TaskComplexity.HIGH,
        cost_tier=CostTier.LOW,
        description="Slower o3-mini variant, 50% cheaper, optimized for cost"
    ),

    # o3-mini - Medium-cost reasoning
    "o3-mini": ModelConfig(
        model_name="o3-mini",
        supports_temperature=False,
        default_temperature=1.0,
        cost_per_1m_input=1.10,
        cost_per_1m_output=4.40,
        max_context=200_000,
        complexity_tier=TaskComplexity.HIGH,
        cost_tier=CostTier.MEDIUM,
        description="Compact reasoning model for complex tasks"
    ),

    # o3 - High-performance reasoning
    "o3": ModelConfig(
        model_name="o3",
        supports_temperature=False,
        default_temperature=1.0,
        cost_per_1m_input=10.00,
        cost_per_1m_output=40.00,
        max_context=200_000,
        complexity_tier=TaskComplexity.VERY_HIGH,
        cost_tier=CostTier.HIGH,
        description="Most capable reasoning model for complex synthesis"
    ),

    # GPT-4o - Stable fallback
    "gpt-4o": ModelConfig(
        model_name="gpt-4o",
        supports_temperature=True,
        default_temperature=0.3,
        cost_per_1m_input=5.00,
        cost_per_1m_output=15.00,
        max_context=128_000,
        complexity_tier=TaskComplexity.VERY_HIGH,
        cost_tier=CostTier.MEDIUM,
        description="Latest stable GPT-4 optimized model"
    ),
}


# =============================================================================
# Task-Specific Model Assignments
# =============================================================================

TASK_MODEL_ASSIGNMENTS = {
    "mood_analysis": "gpt-4o-mini",
    "topic_extraction": "gpt-4o-mini",
    "breakthrough_detection": "o3-mini-flex",
    "deep_analysis": "o3",
}


# =============================================================================
# Model Selection Logic
# =============================================================================

def get_model_for_task(
    task_name: str,
    override_model: Optional[str] = None
) -> ModelConfig:
    """
    Get optimal model configuration for a specific task.

    Args:
        task_name: Task identifier (e.g., 'mood_analysis')
        override_model: Optional model override (for testing/debugging)

    Returns:
        ModelConfig for the selected model

    Raises:
        ValueError: If task or model not found
    """
    # Use override if provided
    if override_model:
        if override_model not in MODEL_REGISTRY:
            raise ValueError(f"Unknown model: {override_model}")
        return MODEL_REGISTRY[override_model]

    # Use task-specific assignment
    if task_name not in TASK_MODEL_ASSIGNMENTS:
        raise ValueError(f"Unknown task: {task_name}. Valid tasks: {list(TASK_MODEL_ASSIGNMENTS.keys())}")

    model_name = TASK_MODEL_ASSIGNMENTS[task_name]
    return MODEL_REGISTRY[model_name]


def get_openai_params(
    task_name: str,
    override_model: Optional[str] = None,
    override_temperature: Optional[float] = None
) -> Dict[str, Any]:
    """
    Get OpenAI API parameters for a specific task.

    Args:
        task_name: Task identifier
        override_model: Optional model override
        override_temperature: Optional temperature override

    Returns:
        Dict with 'model' and 'temperature' keys
    """
    config = get_model_for_task(task_name, override_model)

    # Determine temperature
    if override_temperature is not None:
        if not config.supports_temperature and override_temperature != 1.0:
            raise ValueError(
                f"Model {config.model_name} only supports temperature=1.0. "
                f"Requested: {override_temperature}"
            )
        temperature = override_temperature
    else:
        temperature = config.default_temperature

    return {
        "model": config.model_name,
        "temperature": temperature
    }


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
    """
    config = get_model_for_task(task_name, override_model)

    input_cost = (input_tokens / 1_000_000) * config.cost_per_1m_input
    output_cost = (output_tokens / 1_000_000) * config.cost_per_1m_output

    return input_cost + output_cost
```

### Updated Service Files

Each service will be updated to use the configuration system:

**Example Pattern** (apply to all 4 services):

```python
from app.config.model_config import get_openai_params

class MoodAnalyzer:
    def __init__(self, api_key: Optional[str] = None, override_model: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required")

        openai.api_key = self.api_key

        # Use configuration system
        self.params = get_openai_params("mood_analysis", override_model=override_model)
        self.model = self.params["model"]
        self.temperature = self.params["temperature"]
```

### Verification

**How to verify the desired end state:**

1. **Run Test Suite**:
   ```bash
   cd backend
   source venv/bin/activate
   python tests/test_all_algorithms_detailed.py
   ```

2. **Expected Output**:
   - ✅ Mood Analysis: Success (using gpt-4o-mini)
   - ✅ Topic Extraction: Success (using gpt-4o-mini)
   - ✅ Breakthrough Detection: Success (using o3-mini-flex)
   - ✅ Technique Validation: Success

3. **Verify JSON Output** (`mock-therapy-data/session_03_all_algorithms_output.json`):
   - All 4 algorithms show `"success": true`
   - Mood score between 0-10
   - 1-2 topics extracted
   - Breakthrough detected (if present)
   - Technique validated

4. **Cost Verification**:
   ```bash
   python tests/test_cost_estimation.py
   ```
   - Expected cost per session: ~$0.03-0.05 (massive savings from current $0.15+)

## What We're NOT Doing

**Explicitly out of scope:**

1. ❌ **Not implementing batching** - Each session analyzed individually (could be future optimization)
2. ❌ **Not adding model fine-tuning** - Using base models only
3. ❌ **Not implementing custom model selection UI** - Configuration is code-only
4. ❌ **Not adding streaming responses** - Batch processing with complete responses
5. ❌ **Not migrating to Claude/Anthropic models** - OpenAI-only for now
6. ❌ **Not implementing caching** - OpenAI's native prompt caching not yet integrated
7. ❌ **Not changing algorithm logic** - Only model selection, not analysis methods
8. ❌ **Not updating database schema** - No new fields needed

## Implementation Approach

**Strategy:**

1. **Create configuration system first** - Centralized source of truth
2. **Update services incrementally** - One service at a time to verify
3. **Test after each service** - Ensure no regressions
4. **Run full pipeline test** - Verify Wave 1 + Wave 2 integration

**Rationale:**

- Configuration-driven approach enables easy model swapping
- Incremental updates reduce risk of breaking existing functionality
- Temperature handling is critical (o-series vs GPT-series difference)
- Cost optimization achieved through strategic model selection

---

## Phase 1: Configuration System Setup

### Overview
Create centralized model configuration system with registry, task assignments, and helper functions.

### Changes Required:

#### 1.1 Create Model Configuration Module

**File**: `backend/app/config/model_config.py`
**Changes**: Create new file with complete configuration system

```python
# Full code from "Configuration System Architecture" section above
# (see lines 134-330 of this plan)
```

**Testing approach**:
```python
# Quick test
from app.config.model_config import get_model_for_task, get_openai_params

config = get_model_for_task("mood_analysis")
print(f"Mood Analysis: {config.model_name}, temp={config.default_temperature}")

params = get_openai_params("breakthrough_detection")
print(f"Breakthrough Params: {params}")
```

#### 1.2 Create Configuration Test Suite

**File**: `backend/tests/test_model_config.py`
**Changes**: Create comprehensive configuration tests

```python
"""
Test suite for model configuration system
"""
import pytest
from app.config.model_config import (
    get_model_for_task,
    get_openai_params,
    estimate_cost,
    MODEL_REGISTRY,
    TaskComplexity,
    CostTier
)


def test_model_registry_completeness():
    """Verify all required models are in registry"""
    required_models = [
        "gpt-4o-mini",
        "o3-mini-flex",
        "o3-mini",
        "o3",
        "gpt-4o"
    ]
    for model in required_models:
        assert model in MODEL_REGISTRY


def test_task_assignments():
    """Verify all tasks have model assignments"""
    tasks = ["mood_analysis", "topic_extraction", "breakthrough_detection", "deep_analysis"]
    for task in tasks:
        config = get_model_for_task(task)
        assert config is not None
        assert config.model_name in MODEL_REGISTRY


def test_temperature_handling():
    """Verify temperature constraints are enforced"""
    # o-series models only support temp=1.0
    with pytest.raises(ValueError):
        get_openai_params("breakthrough_detection", override_temperature=0.3)

    # gpt-4o-mini supports custom temperature
    params = get_openai_params("mood_analysis", override_temperature=0.3)
    assert params["temperature"] == 0.3


def test_cost_estimation():
    """Verify cost calculation accuracy"""
    # gpt-4o-mini: $0.15 input, $0.60 output per 1M tokens
    cost = estimate_cost("mood_analysis", input_tokens=1000, output_tokens=500)
    expected = (1000/1_000_000 * 0.15) + (500/1_000_000 * 0.60)
    assert abs(cost - expected) < 0.0001


def test_model_override():
    """Verify model override functionality"""
    params = get_openai_params("mood_analysis", override_model="o3")
    assert params["model"] == "o3"
    assert params["temperature"] == 1.0  # o3 only supports 1.0


def test_invalid_task():
    """Verify error handling for invalid tasks"""
    with pytest.raises(ValueError, match="Unknown task"):
        get_model_for_task("invalid_task")


def test_invalid_model():
    """Verify error handling for invalid models"""
    with pytest.raises(ValueError, match="Unknown model"):
        get_model_for_task("mood_analysis", override_model="gpt-99")
```

### Success Criteria:

#### Automated Verification:
- [x] Configuration module imports successfully: `python -c "from app.config.model_config import get_model_for_task"`
- [x] All tests pass: `cd backend && source venv/bin/activate && pytest tests/test_model_config.py -v`
- [x] No syntax errors in model_config.py: `python -m py_compile app/config/model_config.py`
- [x] All 4 tasks return valid configs: `python -c "from app.config.model_config import get_model_for_task; [get_model_for_task(t) for t in ['mood_analysis', 'topic_extraction', 'breakthrough_detection', 'deep_analysis']]"`

#### Manual Verification:
- [x] Configuration values match December 2025 OpenAI pricing
- [x] Temperature constraints correctly enforced (o-series = 1.0 only)
- [x] Cost estimates are reasonable (~$0.03-0.05 per session)

**Implementation Note**: After completing this phase and all automated verification passes, proceed directly to Phase 2 (no manual testing needed for config-only changes).

---

## Phase 2: Update Mood Analyzer

### Overview
Migrate `mood_analyzer.py` from hardcoded "gpt-5-mini" to configuration-driven gpt-4o-mini.

### Changes Required:

#### 2.1 Update MoodAnalyzer Class

**File**: `backend/app/services/mood_analyzer.py`
**Changes**: Replace hardcoded model with configuration system

```python
# Line 14-17: Add import
from app.config.model_config import get_openai_params

# Line 46-59: Replace __init__ method
def __init__(self, api_key: Optional[str] = None, override_model: Optional[str] = None):
    """
    Initialize the mood analyzer.

    Args:
        api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
        override_model: Optional model override (for testing). If None, uses config default.
    """
    self.api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not self.api_key:
        raise ValueError("OpenAI API key required for mood analysis")

    openai.api_key = self.api_key

    # Get model configuration
    self.params = get_openai_params("mood_analysis", override_model=override_model)
    self.model = self.params["model"]
    self.temperature = self.params["temperature"]

# Line 92-106: Update API call to use dynamic temperature
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
    temperature=self.temperature,  # Use dynamic temperature from config
    response_format={"type": "json_object"}
)
```

#### 2.2 Update Convenience Function

**File**: `backend/app/services/mood_analyzer.py`
**Changes**: Add override_model parameter to convenience function

```python
# Line 217-237: Update convenience function signature
def analyze_mood(
    session_id: str,
    segments: List[Dict[str, Any]],
    patient_speaker_id: str = "SPEAKER_01",
    api_key: Optional[str] = None,
    override_model: Optional[str] = None  # NEW PARAMETER
) -> MoodAnalysis:
    """
    Convenience function to analyze mood for a single session.

    Args:
        session_id: Unique session identifier
        segments: Transcript segments
        patient_speaker_id: Speaker ID for patient
        api_key: Optional OpenAI API key
        override_model: Optional model override (for testing)

    Returns:
        MoodAnalysis object
    """
    analyzer = MoodAnalyzer(api_key=api_key, override_model=override_model)
    return analyzer.analyze_session_mood(session_id, segments, patient_speaker_id)
```

### Success Criteria:

#### Automated Verification:
- [x] Mood analyzer imports successfully: `python -c "from app.services.mood_analyzer import MoodAnalyzer"`
- [x] Test passes: `cd backend && source venv/bin/activate && python tests/test_mood_analysis.py`
- [x] Configuration integration works: `python -c "from app.services.mood_analyzer import MoodAnalyzer; a = MoodAnalyzer(); assert a.model == 'gpt-4o-mini'"`

#### Manual Verification:
- [ ] Mood score is valid (0.0-10.0 in 0.5 increments)
- [ ] Rationale is clinically appropriate
- [ ] Key indicators are specific and evidence-based
- [ ] Emotional tone matches transcript content

**Implementation Note**: After completing automated verification, run manual test on session_03 to verify mood analysis quality before proceeding to Phase 3.

---

## Phase 3: Update Topic Extractor

### Overview
Migrate `topic_extractor.py` from hardcoded "gpt-5-mini" to configuration-driven gpt-4o-mini.

### Changes Required:

#### 3.1 Update TopicExtractor Class

**File**: `backend/app/services/topic_extractor.py`
**Changes**: Replace hardcoded model with configuration system

```python
# Line 19-20: Add import
from app.config.model_config import get_openai_params

# Line 49-62: Replace __init__ method
def __init__(self, api_key: Optional[str] = None, override_model: Optional[str] = None):
    """
    Initialize the topic extractor with technique library.

    Args:
        api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
        override_model: Optional model override (for testing). If None, uses config default.
    """
    self.api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not self.api_key:
        raise ValueError("OpenAI API key required for topic extraction")

    openai.api_key = self.api_key

    # Get model configuration
    self.params = get_openai_params("topic_extraction", override_model=override_model)
    self.model = self.params["model"]
    self.temperature = self.params["temperature"]

    # Load technique library for validation
    self.technique_library: TechniqueLibrary = get_technique_library()

# Line 96-110: Update API call to use dynamic temperature
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
    temperature=self.temperature,  # Use dynamic temperature from config
    response_format={"type": "json_object"}
)
```

#### 3.2 Update Convenience Function

**File**: `backend/app/services/topic_extractor.py`
**Changes**: Add override_model parameter

```python
# Line 337-358: Update convenience function signature
def extract_session_metadata(
    session_id: str,
    segments: List[Dict[str, Any]],
    speaker_roles: Optional[Dict[str, str]] = None,
    api_key: Optional[str] = None,
    override_model: Optional[str] = None  # NEW PARAMETER
) -> SessionMetadata:
    """
    Convenience function to extract metadata for a single session.

    Args:
        session_id: Unique session identifier
        segments: Transcript segments
        speaker_roles: Optional speaker role mapping
        api_key: Optional OpenAI API key
        override_model: Optional model override (for testing)

    Returns:
        SessionMetadata object
    """
    extractor = TopicExtractor(api_key=api_key, override_model=override_model)
    return extractor.extract_metadata(session_id, segments, speaker_roles)
```

### Success Criteria:

#### Automated Verification:
- [ ] Topic extractor imports successfully: `python -c "from app.services.topic_extractor import TopicExtractor"`
- [ ] Test passes: `cd backend && source venv/bin/activate && python tests/test_topic_extraction.py`
- [ ] Configuration integration works: `python -c "from app.services.topic_extractor import TopicExtractor; t = TopicExtractor(); assert t.model == 'gpt-4o-mini'"`

#### Manual Verification:
- [ ] 1-2 specific topics extracted (not vague)
- [ ] 2 actionable homework items identified
- [ ] Technique is from validated library
- [ ] Summary is ≤150 characters
- [ ] Summary uses direct, active voice (not "The session focused on...")

**Implementation Note**: After completing automated verification, run manual test on session_03 to verify extraction quality before proceeding to Phase 4.

---

## Phase 4: Update Breakthrough Detector

### Overview
Migrate `breakthrough_detector.py` from hardcoded "gpt-5" to configuration-driven o3-mini-flex.

### Changes Required:

#### 4.1 Update BreakthroughDetector Class

**File**: `backend/app/services/breakthrough_detector.py`
**Changes**: Replace hardcoded model with configuration system, handle temperature constraint

```python
# Line 14-15: Add import
from app.config.model_config import get_openai_params

# Line 53-65: Replace __init__ method
def __init__(self, api_key: Optional[str] = None, override_model: Optional[str] = None):
    """
    Initialize with OpenAI API key and model selection.

    Args:
        api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
        override_model: Optional model override (for testing). If None, uses config default.
    """
    self.api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not self.api_key:
        raise ValueError("OpenAI API key required for breakthrough detection")

    openai.api_key = self.api_key

    # Get model configuration
    self.params = get_openai_params("breakthrough_detection", override_model=override_model)
    self.model = self.params["model"]
    self.temperature = self.params["temperature"]

# Line 166-175: Update API call to use dynamic temperature
response = openai.chat.completions.create(
    model=self.model,  # Dynamic model from config
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Analyze this therapy session transcript:\n\n{conversation_text}"}
    ],
    temperature=self.temperature,  # Dynamic temperature from config (will be 1.0 for o3-mini-flex)
    response_format={"type": "json_object"}
)
```

**IMPORTANT NOTE**: o3-mini-flex only supports `temperature=1.0`. The configuration system will automatically enforce this, but the algorithm prompt should be robust to temperature variation.

### Success Criteria:

#### Automated Verification:
- [ ] Breakthrough detector imports successfully: `python -c "from app.services.breakthrough_detector import BreakthroughDetector"`
- [ ] Test passes: `cd backend && source venv/bin/activate && python tests/test_breakthrough_detection.py`
- [ ] Configuration integration works: `python -c "from app.services.breakthrough_detector import BreakthroughDetector; b = BreakthroughDetector(); assert b.model == 'o3-mini-flex'"`
- [ ] Temperature is 1.0: `python -c "from app.services.breakthrough_detector import BreakthroughDetector; b = BreakthroughDetector(); assert b.temperature == 1.0"`

#### Manual Verification:
- [ ] Breakthrough detection is highly selective (most sessions = no breakthrough)
- [ ] Detected breakthroughs are POSITIVE SELF-DISCOVERIES (not just emotional moments)
- [ ] Confidence scores are appropriate (0.8+ for genuine breakthroughs)
- [ ] Label is 2-3 words and descriptive (e.g., "ADHD Discovery")
- [ ] Evidence includes specific quotes with timestamps

**Implementation Note**: After completing automated verification, run manual test on session_03 (should detect ADHD discovery breakthrough) and session_01 (crisis session, should NOT detect breakthrough) before proceeding to Phase 5.

---

## Phase 5: Update Deep Analyzer

### Overview
Migrate `deep_analyzer.py` from hardcoded "gpt-4o" to configuration-driven o3.

### Changes Required:

#### 5.1 Update DeepAnalyzer Class

**File**: `backend/app/services/deep_analyzer.py`
**Changes**: Replace hardcoded model with configuration system

```python
# Line 24-25: Add import
from app.config.model_config import get_openai_params

# Line 119-133: Replace __init__ method
def __init__(self, api_key: Optional[str] = None, override_model: Optional[str] = None, db: Optional[Client] = None):
    """
    Initialize the deep analyzer.

    Args:
        api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
        override_model: Optional model override (for testing). If None, uses config default.
        db: Supabase client. If None, uses default from get_db()
    """
    self.api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not self.api_key:
        raise ValueError("OpenAI API key required for deep analysis")

    openai.api_key = self.api_key

    # Get model configuration
    self.params = get_openai_params("deep_analysis", override_model=override_model)
    self.model = self.params["model"]
    self.temperature = self.params["temperature"]

    self.db = db or next(get_db())

# Line 159-174: Update API call to use dynamic temperature
response = openai.chat.completions.create(
    model=self.model,  # Dynamic model from config
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
    temperature=self.temperature,  # Dynamic temperature from config (will be 1.0 for o3)
    response_format={"type": "json_object"}
)
```

#### 5.2 Update Convenience Function

**File**: `backend/app/services/deep_analyzer.py`
**Changes**: Add override_model parameter

```python
# Line 651-669: Update convenience function signature
async def analyze_session_deep(
    session_id: str,
    session: Dict[str, Any],
    api_key: Optional[str] = None,
    override_model: Optional[str] = None  # NEW PARAMETER
) -> DeepAnalysis:
    """
    Convenience function to perform deep analysis on a session.

    Args:
        session_id: Session UUID
        session: Session data
        api_key: Optional OpenAI API key
        override_model: Optional model override (for testing)

    Returns:
        DeepAnalysis object
    """
    analyzer = DeepAnalyzer(api_key=api_key, override_model=override_model)
    return await analyzer.analyze_session(session_id, session)
```

**IMPORTANT NOTE**: o3 only supports `temperature=1.0`. The configuration system will automatically enforce this. Deep analysis prompts should be designed to handle this constraint.

### Success Criteria:

#### Automated Verification:
- [ ] Deep analyzer imports successfully: `python -c "from app.services.deep_analyzer import DeepAnalyzer"`
- [ ] Configuration integration works: `python -c "from app.services.deep_analyzer import DeepAnalyzer; d = DeepAnalyzer(); assert d.model == 'o3'"`
- [ ] Temperature is 1.0: `python -c "from app.services.deep_analyzer import DeepAnalyzer; d = DeepAnalyzer(); assert d.temperature == 1.0"`

#### Manual Verification:
- [ ] Deep analysis includes progress indicators with specific evidence
- [ ] Therapeutic insights are patient-empowering and compassionate
- [ ] Coping skills proficiency levels are accurate
- [ ] Therapeutic relationship assessment is evidence-based
- [ ] Recommendations are specific, actionable, and encouraging
- [ ] Confidence score reflects data quality (0.7-0.9 range typical)

**Implementation Note**: After completing automated verification, run manual test on session_03 (requires Wave 1 complete first) to verify deep analysis quality before proceeding to Phase 6.

---

## Phase 6: Full Pipeline Integration Test

### Overview
Test complete 2-wave pipeline with all updated services to ensure proper integration and cost optimization.

### Changes Required:

#### 6.1 Create Comprehensive Demo Script

**File**: `backend/tests/test_optimized_pipeline_demo.py`
**Changes**: Create new test demonstrating all algorithms with new models

```python
"""
Optimized Pipeline Demo - December 2025 Models

Demonstrates all 4 algorithms running with optimized model selection:
- Mood Analysis: gpt-4o-mini
- Topic Extraction: gpt-4o-mini
- Breakthrough Detection: o3-mini-flex
- Deep Analysis: o3 (requires Wave 1 complete)

Saves results to both terminal (formatted) and JSON (detailed).
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.mood_analyzer import MoodAnalyzer
from app.services.topic_extractor import TopicExtractor
from app.services.breakthrough_detector import BreakthroughDetector
from app.config.model_config import get_model_for_task, estimate_cost


def load_session(session_file: Path) -> dict:
    """Load session data from JSON file"""
    with open(session_file, 'r') as f:
        return json.load(f)


def serialize_datetime(obj):
    """JSON serializer for datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def format_cost(cost_usd: float) -> str:
    """Format cost in USD cents"""
    return f"${cost_usd:.4f} ({cost_usd * 100:.2f}¢)"


def main():
    """Run optimized pipeline demo"""
    print("=" * 80)
    print("OPTIMIZED PIPELINE DEMO - December 2025 Models")
    print("=" * 80)
    print()

    # Load session
    session_file = Path(__file__).parent.parent.parent / "mock-therapy-data" / "sessions" / "session_03_adhd_discovery.json"
    session = load_session(session_file)
    segments = session['segments']
    session_id = session['id']

    # Session info
    print(f"Session: {session['filename']}")
    print(f"Duration: {session['metadata']['duration'] / 60:.1f} minutes")
    print(f"Segments: {session['quality']['total_segments']} total (Therapist: {session['quality']['speaker_segment_distribution']['SPEAKER_00']}, Client: {session['quality']['speaker_segment_distribution']['SPEAKER_01']})")
    print()

    results = {
        "test_metadata": {
            "session_id": session_id,
            "session_file": "session_03_adhd_discovery.json",
            "test_run_at": datetime.utcnow().isoformat(),
            "pipeline_type": "optimized_december_2025"
        },
        "model_assignments": {
            "mood_analysis": get_model_for_task("mood_analysis").model_name,
            "topic_extraction": get_model_for_task("topic_extraction").model_name,
            "breakthrough_detection": get_model_for_task("breakthrough_detection").model_name,
        },
        "algorithms": {}
    }

    total_cost = 0.0

    # Algorithm 1: Mood Analysis
    print("-" * 80)
    print("MOOD ANALYSIS (gpt-4o-mini)")
    print("-" * 80)
    try:
        analyzer = MoodAnalyzer()
        print(f"Model: {analyzer.model}, Temperature: {analyzer.temperature}")

        mood_result = analyzer.analyze_session_mood(session_id, segments, "SPEAKER_01")

        # Estimate cost (approximate token counts)
        input_tokens = len(json.dumps(segments)) // 4  # Rough estimate
        output_tokens = 200  # Typical mood analysis output
        cost = estimate_cost("mood_analysis", input_tokens, output_tokens)
        total_cost += cost

        print(f"✓ SUCCESS")
        print(f"  Mood Score: {mood_result.mood_score}/10.0")
        print(f"  Confidence: {mood_result.confidence:.2f}")
        print(f"  Emotional Tone: {mood_result.emotional_tone}")
        print(f"  Rationale: {mood_result.rationale[:100]}...")
        print(f"  Key Indicators: {len(mood_result.key_indicators)} signals")
        print(f"  Estimated Cost: {format_cost(cost)}")

        results["algorithms"]["mood_analysis"] = {
            "success": True,
            "model": analyzer.model,
            "temperature": analyzer.temperature,
            "output": {
                "mood_score": mood_result.mood_score,
                "confidence": mood_result.confidence,
                "emotional_tone": mood_result.emotional_tone,
                "rationale": mood_result.rationale,
                "key_indicators": mood_result.key_indicators
            },
            "estimated_cost_usd": cost
        }
    except Exception as e:
        print(f"✗ FAILED: {e}")
        results["algorithms"]["mood_analysis"] = {"success": False, "error": str(e)}

    print()

    # Algorithm 2: Topic Extraction
    print("-" * 80)
    print("TOPIC EXTRACTION (gpt-4o-mini)")
    print("-" * 80)
    try:
        extractor = TopicExtractor()
        print(f"Model: {extractor.model}, Temperature: {extractor.temperature}")

        topic_result = extractor.extract_metadata(
            session_id,
            segments,
            {"SPEAKER_00": "Therapist", "SPEAKER_01": "Client"}
        )

        # Estimate cost
        input_tokens = len(json.dumps(segments)) // 4
        output_tokens = 300  # Typical topic extraction output
        cost = estimate_cost("topic_extraction", input_tokens, output_tokens)
        total_cost += cost

        print(f"✓ SUCCESS")
        print(f"  Topics: {', '.join(topic_result.topics)}")
        print(f"  Action Items: {len(topic_result.action_items)} items")
        print(f"  Technique: {topic_result.technique}")
        print(f"  Summary: {topic_result.summary} ({len(topic_result.summary)} chars)")
        print(f"  Confidence: {topic_result.confidence:.2f}")
        print(f"  Estimated Cost: {format_cost(cost)}")

        results["algorithms"]["topic_extraction"] = {
            "success": True,
            "model": extractor.model,
            "temperature": extractor.temperature,
            "output": {
                "topics": topic_result.topics,
                "action_items": topic_result.action_items,
                "technique": topic_result.technique,
                "summary": topic_result.summary,
                "confidence": topic_result.confidence
            },
            "estimated_cost_usd": cost
        }
    except Exception as e:
        print(f"✗ FAILED: {e}")
        results["algorithms"]["topic_extraction"] = {"success": False, "error": str(e)}

    print()

    # Algorithm 3: Breakthrough Detection
    print("-" * 80)
    print("BREAKTHROUGH DETECTION (o3-mini-flex)")
    print("-" * 80)
    try:
        detector = BreakthroughDetector()
        print(f"Model: {detector.model}, Temperature: {detector.temperature}")

        bt_result = detector.analyze_session(segments, {"session_id": session_id})

        # Estimate cost
        input_tokens = len(json.dumps(segments)) // 4
        output_tokens = 400  # Typical breakthrough output
        cost = estimate_cost("breakthrough_detection", input_tokens, output_tokens)
        total_cost += cost

        print(f"✓ SUCCESS")
        print(f"  Breakthroughs Found: {len(bt_result.breakthrough_candidates)}")
        if bt_result.primary_breakthrough:
            bt = bt_result.primary_breakthrough
            print(f"  Primary Breakthrough:")
            print(f"    Type: {bt.breakthrough_type}")
            print(f"    Confidence: {bt.confidence_score:.2f}")
            print(f"    Description: {bt.description[:150]}...")
            print(f"    Timestamp: {bt.timestamp_start:.0f}s - {bt.timestamp_end:.0f}s")
        else:
            print(f"  No breakthrough detected (session focused on skill-building)")
        print(f"  Estimated Cost: {format_cost(cost)}")

        results["algorithms"]["breakthrough_detection"] = {
            "success": True,
            "model": detector.model,
            "temperature": detector.temperature,
            "output": {
                "has_breakthrough": bt_result.has_breakthrough,
                "breakthrough_count": len(bt_result.breakthrough_candidates),
                "primary_breakthrough": {
                    "type": bt_result.primary_breakthrough.breakthrough_type,
                    "confidence": bt_result.primary_breakthrough.confidence_score,
                    "description": bt_result.primary_breakthrough.description
                } if bt_result.primary_breakthrough else None
            },
            "estimated_cost_usd": cost
        }
    except Exception as e:
        print(f"✗ FAILED: {e}")
        results["algorithms"]["breakthrough_detection"] = {"success": False, "error": str(e)}

    print()

    # Summary
    print("=" * 80)
    print("PIPELINE SUMMARY")
    print("=" * 80)
    print(f"Total Estimated Cost: {format_cost(total_cost)}")
    print()
    print("Algorithm Status:")
    for algo, data in results["algorithms"].items():
        status = "✓" if data.get("success") else "✗"
        model = data.get("model", "N/A")
        cost = data.get("estimated_cost_usd", 0)
        print(f"  {status} {algo.replace('_', ' ').title()}: {model} ({format_cost(cost)})")

    # Save results
    output_file = Path(__file__).parent.parent.parent / "mock-therapy-data" / "optimized_pipeline_demo_output.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=serialize_datetime)

    print()
    print(f"✓ Detailed output saved to: {output_file.name}")


if __name__ == "__main__":
    main()
```

#### 6.2 Update Existing Test Script

**File**: `backend/tests/test_all_algorithms_detailed.py`
**Changes**: Update to use new model configuration

```python
# Line 75-79: Add model information to output
results["model_info"] = {
    "mood_analysis_model": analyzer.model if 'analyzer' in locals() else None,
    "topic_extraction_model": extractor.model if 'extractor' in locals() else None,
    "breakthrough_detection_model": detector.model if 'detector' in locals() else None,
}
```

### Success Criteria:

#### Automated Verification:
- [ ] Demo script runs successfully: `cd backend && source venv/bin/activate && python tests/test_optimized_pipeline_demo.py`
- [ ] All 3 algorithms complete successfully (no errors)
- [ ] JSON output file is created: `ls -la mock-therapy-data/optimized_pipeline_demo_output.json`
- [ ] Total cost is under $0.05 per session

#### Manual Verification:
- [ ] Terminal output is readable and informative
- [ ] Model assignments match expected values:
  - Mood Analysis: gpt-4o-mini
  - Topic Extraction: gpt-4o-mini
  - Breakthrough Detection: o3-mini-flex
- [ ] All results are clinically appropriate and high-quality
- [ ] Cost estimates are reasonable (~3-5 cents per session)

**Implementation Note**: After completing this phase, the optimized pipeline is ready for production use. Proceed to Phase 7 for documentation.

---

## Phase 7: Documentation & Migration Guide

### Overview
Create comprehensive documentation for the new model configuration system and provide migration guide for future model updates.

### Changes Required:

#### 7.1 Create Model Configuration README

**File**: `backend/app/config/README.md`
**Changes**: Create new documentation file

```markdown
# Model Configuration System

## Overview

Centralized OpenAI model selection and configuration for TherapyBridge AI analysis pipeline.

## Quick Start

```python
from app.config.model_config import get_model_for_task, get_openai_params

# Get model configuration for a task
config = get_model_for_task("mood_analysis")
print(f"Model: {config.model_name}, Cost: ${config.cost_per_1m_input}/1M input tokens")

# Get OpenAI API parameters
params = get_openai_params("breakthrough_detection")
# Returns: {"model": "o3-mini-flex", "temperature": 1.0}
```

## Current Model Assignments (December 2025)

| Task | Model | Input Cost | Output Cost | Rationale |
|------|-------|------------|-------------|-----------|
| Mood Analysis | gpt-4o-mini | $0.15/1M | $0.60/1M | Simple scoring, ultra-low-cost |
| Topic Extraction | gpt-4o-mini | $0.15/1M | $0.60/1M | Structured extraction, cost-optimized |
| Breakthrough Detection | o3-mini-flex | $0.55/1M | $2.20/1M | Complex reasoning, balanced cost |
| Deep Analysis | o3 | $10/1M | $40/1M | Highest complexity synthesis |

**Estimated cost per session**: ~$0.03-0.05 (3-5 cents)

## Temperature Constraints

**Important**: o-series models (o3, o3-mini, o3-mini-flex, o4-mini) **only support temperature=1.0**.

Attempting to use custom temperature values will result in:
```
Error code: 400 - Unsupported value: 'temperature' does not support 0.3 with this model.
```

The configuration system automatically enforces this constraint.

## Model Override (Testing)

Override models for testing or debugging:

```python
from app.services.mood_analyzer import MoodAnalyzer

# Use gpt-4o instead of default gpt-4o-mini
analyzer = MoodAnalyzer(override_model="gpt-4o")
```

## Adding New Models

1. **Update MODEL_REGISTRY** in `model_config.py`:

```python
"new-model-name": ModelConfig(
    model_name="new-model-name",
    supports_temperature=True,  # Check OpenAI docs
    default_temperature=0.3,
    cost_per_1m_input=1.00,
    cost_per_1m_output=3.00,
    max_context=128_000,
    complexity_tier=TaskComplexity.MEDIUM,
    cost_tier=CostTier.MEDIUM,
    description="Model description"
)
```

2. **Update TASK_MODEL_ASSIGNMENTS** (if changing default):

```python
TASK_MODEL_ASSIGNMENTS = {
    "mood_analysis": "new-model-name",  # Changed from gpt-4o-mini
    # ...
}
```

3. **Run tests** to verify:

```bash
pytest tests/test_model_config.py -v
python tests/test_optimized_pipeline_demo.py
```

## Cost Estimation

Estimate costs before running analysis:

```python
from app.config.model_config import estimate_cost

# Typical therapy session: ~2000 input tokens, ~300 output tokens
cost = estimate_cost("mood_analysis", input_tokens=2000, output_tokens=300)
print(f"Estimated cost: ${cost:.4f}")
```

## Migration Guide

### From Hardcoded Models to Config System

**Before** (old code):
```python
class MoodAnalyzer:
    def __init__(self, api_key=None, model="gpt-4o-mini"):
        self.model = model
        self.temperature = 0.3
```

**After** (new code):
```python
from app.config.model_config import get_openai_params

class MoodAnalyzer:
    def __init__(self, api_key=None, override_model=None):
        self.params = get_openai_params("mood_analysis", override_model=override_model)
        self.model = self.params["model"]
        self.temperature = self.params["temperature"]
```

## Troubleshooting

**Problem**: `ValueError: Unknown model: gpt-5-mini`
**Solution**: Model doesn't exist. Check MODEL_REGISTRY for valid models.

**Problem**: `400 error: temperature not supported`
**Solution**: You're using an o-series model. Set `override_temperature=None` to use default (1.0).

**Problem**: Costs are higher than expected
**Solution**: Check token usage with `response.usage.total_tokens`. Consider using cheaper model tier.

## References

- OpenAI Pricing: https://openai.com/api/pricing/
- Model Documentation: https://platform.openai.com/docs/models
- Configuration Code: `backend/app/config/model_config.py`
```

#### 7.2 Update Main README

**File**: `backend/README.md`
**Changes**: Add section about model configuration

```markdown
## AI Model Configuration

TherapyBridge uses a centralized model configuration system optimized for cost and quality.

**Current Models** (December 2025):
- **Mood Analysis**: gpt-4o-mini ($0.15/1M input tokens)
- **Topic Extraction**: gpt-4o-mini ($0.15/1M input tokens)
- **Breakthrough Detection**: o3-mini-flex ($0.55/1M input tokens)
- **Deep Analysis**: o3 ($10/1M input tokens)

**Average cost per session**: ~$0.03-0.05

See `app/config/README.md` for full documentation.
```

### Success Criteria:

#### Automated Verification:
- [ ] README files exist: `ls backend/app/config/README.md backend/README.md`
- [ ] Markdown is valid: Check for broken links or formatting issues

#### Manual Verification:
- [ ] Documentation is clear and comprehensive
- [ ] Code examples are accurate and runnable
- [ ] Cost estimates match current OpenAI pricing
- [ ] Migration guide is helpful for future updates

**Implementation Note**: After completing this phase, the implementation is fully complete. Proceed to final testing and deployment.

---

## Testing Strategy

### Unit Tests

**Test Coverage**:
1. **Model Configuration** (`test_model_config.py`):
   - Registry completeness (all required models present)
   - Task assignments (all tasks have models)
   - Temperature constraints (o-series vs GPT-series)
   - Cost estimation accuracy
   - Model override functionality
   - Error handling (invalid tasks, invalid models)

2. **Service Integration** (existing test files updated):
   - `test_mood_analysis.py` - Verify gpt-4o-mini usage
   - `test_topic_extraction.py` - Verify gpt-4o-mini usage
   - `test_breakthrough_detection.py` - Verify o3-mini-flex usage

### Integration Tests

**End-to-End Pipeline**:
1. Run `test_optimized_pipeline_demo.py` on multiple sessions:
   - session_01 (crisis intake - no breakthrough expected)
   - session_03 (ADHD discovery - breakthrough expected)
   - session_06 (spring break hope - mood improvement)
   - session_12 (thriving - positive progress)

2. Verify:
   - All 4 algorithms complete successfully
   - Results are clinically appropriate
   - Cost is under $0.05 per session
   - No temperature-related errors

### Manual Testing Steps

**Before Deployment**:

1. **Test on Session 03 (ADHD Discovery)**:
   ```bash
   cd backend
   source venv/bin/activate
   python tests/test_optimized_pipeline_demo.py
   ```
   - Verify mood score reflects patient distress (4-5 range)
   - Verify topics include "ADHD" and "Self-Compassion"
   - Verify breakthrough detected (ADHD reframing)
   - Verify technique is validated from library

2. **Test on Session 01 (Crisis Intake)**:
   - Verify low mood score (2-3 range)
   - Verify topics include "Suicidal Ideation"
   - Verify NO breakthrough detected (crisis intervention ≠ discovery)

3. **Test Cost Estimation**:
   ```bash
   python -c "from app.config.model_config import estimate_cost; print(f'Mood: ${estimate_cost(\"mood_analysis\", 2000, 300):.4f}'); print(f'Topics: ${estimate_cost(\"topic_extraction\", 2000, 300):.4f}'); print(f'Breakthrough: ${estimate_cost(\"breakthrough_detection\", 2000, 400):.4f}')"
   ```
   - Verify total is under $0.03

4. **Test Model Override**:
   ```python
   from app.services.mood_analyzer import MoodAnalyzer
   analyzer = MoodAnalyzer(override_model="gpt-4o")
   assert analyzer.model == "gpt-4o"
   ```

## Performance Considerations

### Cost Optimization

**Baseline Costs** (estimated per session):
- Mood Analysis: ~$0.003 (0.3¢)
- Topic Extraction: ~$0.004 (0.4¢)
- Breakthrough Detection: ~$0.011 (1.1¢)
- Deep Analysis: ~$0.200 (20¢) - only if Wave 1 triggers it

**Total per session**: ~$0.218 (21.8¢) with deep analysis, ~$0.018 (1.8¢) without

**Optimization Strategies**:
1. **Skip deep analysis for low-quality sessions** - Check confidence scores from Wave 1
2. **Use batch API** (50% discount) - For non-real-time processing
3. **Implement prompt caching** - Future optimization (75% discount on cached inputs)

### Latency Considerations

**Expected Response Times**:
- gpt-4o-mini: ~2-5 seconds
- o3-mini-flex: ~10-20 seconds (slower for 50% cost savings)
- o3: ~15-30 seconds (complex reasoning)

**Wave 1 (parallel)**: ~10-20 seconds total (limited by slowest, likely breakthrough)
**Wave 2 (sequential)**: ~15-30 seconds (deep analysis)
**Total pipeline**: ~25-50 seconds per session

## Migration Notes

### Backwards Compatibility

**Breaking Changes**:
- ❌ Services no longer accept `model` parameter in `__init__`
- ✅ Services now accept `override_model` parameter instead
- ✅ All existing code using default models will continue to work

**Migration Path**:
```python
# Old code (will break):
analyzer = MoodAnalyzer(model="custom-model")

# New code (correct):
analyzer = MoodAnalyzer(override_model="custom-model")
```

### Environment Variables

**No changes required** - `OPENAI_API_KEY` environment variable is still used.

### Database Schema

**No changes required** - This is a code-only update. No database migrations needed.

## References

- **OpenAI Pricing** (December 2025): https://openai.com/api/pricing/
- **OpenAI Models Documentation**: https://platform.openai.com/docs/models
- **o3 Announcement**: https://openai.com/index/introducing-o3-and-o4-mini/
- **GPT-4o-mini Announcement**: https://openai.com/index/gpt-4o-mini-advancing-cost-efficient-intelligence/
- **Configuration Code**: `backend/app/config/model_config.py`
- **Session Log Entry**: `.claude/CLAUDE.md` (Session Log section)

---

**END OF IMPLEMENTATION PLAN**
