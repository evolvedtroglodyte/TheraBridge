"""
Base AI Generator - Abstract Base Class for AI Analysis Services

Provides a unified interface for AI-powered generators with:
- Sync and async client support via Generic typing
- Automatic cost tracking via track_generation_cost()
- MODEL_TIER integration via get_model_name()
- Consistent error handling and logging

Usage:
    # For async services (like MoodAnalyzer)
    class MyAsyncGenerator(BaseAIGenerator[AsyncOpenAI]):
        def get_task_name(self) -> str:
            return "my_task"

        def build_messages(self, context: Dict) -> List[Dict]:
            return [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": self._create_user_prompt(context)}
            ]

    # For sync services (like DeepAnalyzer)
    class MySyncGenerator(BaseAIGenerator[openai.OpenAI]):
        ...
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, Dict, List, Any, Union
from dataclasses import dataclass
from datetime import datetime
import logging
import time
import json
import os

from openai import OpenAI, AsyncOpenAI

from app.config.model_config import (
    get_model_name,
    track_generation_cost,
    GenerationCost,
    ModelTier,
    get_current_tier,
)
from app.config import settings

logger = logging.getLogger(__name__)

# Type variable for sync vs async OpenAI client
ClientType = TypeVar("ClientType", OpenAI, AsyncOpenAI)


@dataclass
class GenerationResult:
    """
    Result from an AI generation.

    Contains both the parsed content and cost tracking info.
    """
    content: Dict[str, Any]  # Parsed JSON response
    cost_info: Optional[GenerationCost] = None
    raw_response: Optional[Any] = None  # Original API response for debugging


class BaseAIGenerator(ABC, Generic[ClientType]):
    """
    Abstract base class for AI-powered generators.

    Provides:
    - Consistent initialization with API key and model override
    - Abstract methods for task-specific behavior
    - Template methods for common API call patterns
    - Cost tracking integration
    - MODEL_TIER support

    Type Parameters:
        ClientType: Either OpenAI (sync) or AsyncOpenAI (async)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        override_model: Optional[str] = None
    ):
        """
        Initialize the generator.

        Args:
            api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
            override_model: Optional model override for testing/experimentation.
        """
        self.api_key = api_key or settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(f"OpenAI API key required for {self.__class__.__name__}")

        self.model = get_model_name(self.get_task_name(), override_model=override_model)
        self._override_model = override_model

        # Client will be set by subclass
        self._client: Optional[ClientType] = None

    @property
    def client(self) -> ClientType:
        """Get the OpenAI client (lazy initialization by subclass)."""
        if self._client is None:
            raise RuntimeError("Client not initialized. Subclass must set self._client.")
        return self._client

    @abstractmethod
    def get_task_name(self) -> str:
        """
        Return the task name for model selection and cost tracking.

        This should match a key in TASK_MODEL_ASSIGNMENTS.

        Returns:
            Task name (e.g., "mood_analysis", "deep_analysis")
        """
        pass

    @abstractmethod
    def build_messages(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Build the messages array for the chat completion API.

        Args:
            context: Context dictionary with all necessary data

        Returns:
            List of message dicts with "role" and "content" keys
        """
        pass

    def get_api_kwargs(self) -> Dict[str, Any]:
        """
        Get additional kwargs for the API call.

        Override to customize (e.g., add response_format, max_tokens).
        Default: returns JSON response format.

        Returns:
            Dict of kwargs to pass to chat.completions.create()
        """
        return {
            "response_format": {"type": "json_object"}
        }

    def parse_response(self, content: str) -> Dict[str, Any]:
        """
        Parse the raw API response content.

        Override for custom parsing logic.

        Args:
            content: Raw string content from API response

        Returns:
            Parsed dictionary
        """
        return json.loads(content)

    def get_current_model(self) -> str:
        """Get the current model name (respects MODEL_TIER)."""
        return self.model

    def get_current_tier(self) -> ModelTier:
        """Get the current MODEL_TIER."""
        return get_current_tier()

    # =========================================================================
    # Template Methods - Sync
    # =========================================================================

    def _call_api_sync(
        self,
        context: Dict[str, Any],
        session_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> GenerationResult:
        """
        Template method for synchronous API calls.

        Handles:
        - Message building
        - API call with timing
        - Cost tracking
        - Response parsing

        Args:
            context: Context for message building
            session_id: Optional session ID for cost tracking
            patient_id: Optional patient ID for cost tracking
            metadata: Optional additional metadata

        Returns:
            GenerationResult with parsed content and cost info
        """
        messages = self.build_messages(context)
        api_kwargs = self.get_api_kwargs()

        start_time = time.time()

        try:
            # NOTE: GPT-5 series does NOT support custom temperature
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **api_kwargs
            )

            # Track cost
            cost_info = track_generation_cost(
                response=response,
                task=self.get_task_name(),
                model=self.model,
                start_time=start_time,
                session_id=session_id,
                patient_id=patient_id,
                metadata=metadata
            )

            # Parse response
            content = self.parse_response(response.choices[0].message.content)

            return GenerationResult(
                content=content,
                cost_info=cost_info,
                raw_response=response
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response for {self.get_task_name()}: {e}")
            raise ValueError(f"Invalid JSON response from API: {e}")
        except Exception as e:
            logger.error(f"{self.get_task_name()} API call failed: {e}")
            raise

    # =========================================================================
    # Template Methods - Async
    # =========================================================================

    async def _call_api_async(
        self,
        context: Dict[str, Any],
        session_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> GenerationResult:
        """
        Template method for asynchronous API calls.

        Handles:
        - Message building
        - API call with timing
        - Cost tracking
        - Response parsing

        Args:
            context: Context for message building
            session_id: Optional session ID for cost tracking
            patient_id: Optional patient ID for cost tracking
            metadata: Optional additional metadata

        Returns:
            GenerationResult with parsed content and cost info
        """
        messages = self.build_messages(context)
        api_kwargs = self.get_api_kwargs()

        start_time = time.time()

        try:
            # NOTE: GPT-5 series does NOT support custom temperature
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **api_kwargs
            )

            # Track cost
            cost_info = track_generation_cost(
                response=response,
                task=self.get_task_name(),
                model=self.model,
                start_time=start_time,
                session_id=session_id,
                patient_id=patient_id,
                metadata=metadata
            )

            # Parse response
            content = self.parse_response(response.choices[0].message.content)

            return GenerationResult(
                content=content,
                cost_info=cost_info,
                raw_response=response
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response for {self.get_task_name()}: {e}")
            raise ValueError(f"Invalid JSON response from API: {e}")
        except Exception as e:
            logger.error(f"{self.get_task_name()} API call failed: {e}")
            raise


class SyncAIGenerator(BaseAIGenerator[OpenAI]):
    """
    Base class for synchronous AI generators.

    Automatically initializes sync OpenAI client.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        override_model: Optional[str] = None
    ):
        super().__init__(api_key=api_key, override_model=override_model)
        self._client = OpenAI(api_key=self.api_key)

    def generate(
        self,
        context: Dict[str, Any],
        session_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> GenerationResult:
        """
        Generate content synchronously.

        Args:
            context: Context for generation
            session_id: Optional session ID for tracking
            patient_id: Optional patient ID for tracking
            metadata: Optional additional metadata

        Returns:
            GenerationResult with content and cost info
        """
        return self._call_api_sync(
            context=context,
            session_id=session_id,
            patient_id=patient_id,
            metadata=metadata
        )


class AsyncAIGenerator(BaseAIGenerator[AsyncOpenAI]):
    """
    Base class for asynchronous AI generators.

    Automatically initializes async OpenAI client.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        override_model: Optional[str] = None
    ):
        super().__init__(api_key=api_key, override_model=override_model)
        self._client = AsyncOpenAI(api_key=self.api_key)

    async def generate(
        self,
        context: Dict[str, Any],
        session_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> GenerationResult:
        """
        Generate content asynchronously.

        Args:
            context: Context for generation
            session_id: Optional session ID for tracking
            patient_id: Optional patient ID for tracking
            metadata: Optional additional metadata

        Returns:
            GenerationResult with content and cost info
        """
        return await self._call_api_async(
            context=context,
            session_id=session_id,
            patient_id=patient_id,
            metadata=metadata
        )
