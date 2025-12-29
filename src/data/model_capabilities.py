from dataclasses import dataclass
from typing import Literal, Optional

from src.data.valid_models import VALID_OA_MODELS, VALID_ANT_MODELS


@dataclass
class ModelCapabilities:
    """Capabilities for a specific model."""
    provider: Literal["openai", "anthropic"]
    supports_streaming: bool = True
    supports_tools: bool = True
    
    # Reasoning/thinking support
    # - "none": No reasoning support
    # - "summary": OpenAI-style (hidden reasoning, summary available)
    # - "extended_thinking": Anthropic-style (full thinking stream visible)
    reasoning_type: Literal["none", "summary", "extended_thinking"] = "none"
    
    # OpenAI reasoning settings
    default_reasoning_effort: Optional[Literal["low", "medium", "high"]] = None
    
    # Anthropic thinking settings
    default_thinking_budget: Optional[int] = None
    
    # Token limits
    default_max_tokens: int = 4096
    max_thinking_tokens: Optional[int] = None  # For extended thinking models


# Model Registry

MODEL_CAPABILITIES: dict[str, ModelCapabilities] = {

    # OpenAI Models - NO reasoning
    "gpt-3.5-turbo": ModelCapabilities(
        provider="openai",
        reasoning_type="none",
        default_max_tokens=4096,
    ),

    "gpt-4": ModelCapabilities(
        provider="openai",
        reasoning_type="none",
        default_max_tokens=8192,
    ),

    "gpt-4o": ModelCapabilities(
        provider="openai",
        reasoning_type="none",
        default_max_tokens=4096,
    ),

    "gpt-4.1": ModelCapabilities(
        provider="openai",
        reasoning_type="none",
        default_max_tokens=8192,
    ),
    
    # OpenAI Models - WITH reasoning (summary only, tokens hidden)
    "gpt-5": ModelCapabilities(
        provider="openai",
        reasoning_type="summary",
        default_reasoning_effort="medium",
        default_max_tokens=16384,
    ),
    "gpt-5.1": ModelCapabilities(
        provider="openai",
        reasoning_type="summary",
        default_reasoning_effort="medium",
        default_max_tokens=16384,
    ),
    "gpt-5.2-chat-latest": ModelCapabilities(
        provider="openai",
        reasoning_type="summary",
        default_reasoning_effort="medium",
        default_max_tokens=16384,
    ),
    
    # -------------------------------------------------------------------------
    # Anthropic Models - ALL support extended thinking
    # -------------------------------------------------------------------------
    "claude-3-opus-latest": ModelCapabilities(
        provider="anthropic",
        reasoning_type="extended_thinking",
        default_thinking_budget=10000,
        default_max_tokens=4096,
        max_thinking_tokens=32000,
    ),
    "claude-3-5-haiku-latest": ModelCapabilities(
        provider="anthropic",
        reasoning_type="extended_thinking",
        default_thinking_budget=8000,
        default_max_tokens=4096,
        max_thinking_tokens=16000,
    ),
    "claude-3-7-sonnet-latest": ModelCapabilities(
        provider="anthropic",
        reasoning_type="extended_thinking",
        default_thinking_budget=10000,
        default_max_tokens=4096,
        max_thinking_tokens=32000,
    ),
    "claude-haiku-4-5": ModelCapabilities(
        provider="anthropic",
        reasoning_type="extended_thinking",
        default_thinking_budget=8000,
        default_max_tokens=4096,
        max_thinking_tokens=16000,
    ),
    "claude-sonnet-4-5-20250929": ModelCapabilities(
        provider="anthropic",
        reasoning_type="extended_thinking",
        default_thinking_budget=10000,
        default_max_tokens=8192,
        max_thinking_tokens=32000,
    ),
    "claude-opus-4-5-20251101": ModelCapabilities(
        provider="anthropic",
        reasoning_type="extended_thinking",
        default_thinking_budget=16000,
        default_max_tokens=8192,
        max_thinking_tokens=64000,
    ),
}


# Helper Functions
def get_capabilities(model: str) -> ModelCapabilities:
    """
    Get capabilities for a model.
    
    Args:
        model: Model name string
        
    Returns:
        ModelCapabilities for the model
        
    Raises:
        ValueError: If model is not recognized
    """
    if model in MODEL_CAPABILITIES:
        return MODEL_CAPABILITIES[model]
    
    # Fallback: try to infer provider from model name
    if model.startswith("gpt"):
        return ModelCapabilities(
            provider="openai",
            reasoning_type="none",
        )
    elif model.startswith("claude"):
        return ModelCapabilities(
            provider="anthropic",
            reasoning_type="extended_thinking",
            default_thinking_budget=10000,
        )
    
    raise ValueError(f"Unknown model: {model}")


def supports_streaming(model: str) -> bool:
    """Check if model supports streaming."""
    return get_capabilities(model).supports_streaming


def supports_thinking(model: str) -> bool:
    """Check if model supports any form of thinking/reasoning."""
    caps = get_capabilities(model)
    return caps.reasoning_type in ("summary", "extended_thinking")


def supports_extended_thinking(model: str) -> bool:
    """Check if model supports full extended thinking (Anthropic-style)."""
    return get_capabilities(model).reasoning_type == "extended_thinking"


def supports_reasoning_summary(model: str) -> bool:
    """Check if model supports reasoning summary (OpenAI-style)."""
    return get_capabilities(model).reasoning_type == "summary"


def get_provider(model: str) -> str:
    """Get the provider for a model."""
    return get_capabilities(model).provider


def is_valid_model(model: str) -> bool:
    """Check if a model is valid."""
    return model in VALID_OA_MODELS or model in VALID_ANT_MODELS
