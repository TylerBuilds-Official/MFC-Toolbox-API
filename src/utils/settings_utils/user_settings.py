from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class UserSettings:
    """Represents a user's settings."""
    user_id: int
    provider: str
    default_model: str
    updated_at: Optional[datetime] = None
    
    # ==========================================================================
    # Streaming & Reasoning Settings
    # TODO: Add these columns to SQL table, using defaults until then
    # ==========================================================================
    enable_streaming: bool = True                   # Stream responses token-by-token
    enable_extended_thinking: bool = False          # Enable thinking/reasoning display
    openai_reasoning_effort: str = "medium"         # low/medium/high for gpt-5+
    anthropic_thinking_budget: int = 10000          # Token budget for Claude thinking

    def to_dict(self) -> dict:
        """Convert to API response format."""
        return {
            "provider": self.provider,
            "default_model": self.default_model,
            
            # Streaming & reasoning
            "enable_streaming": self.enable_streaming,
            "enable_extended_thinking": self.enable_extended_thinking,
            "openai_reasoning_effort": self.openai_reasoning_effort,
            "anthropic_thinking_budget": self.anthropic_thinking_budget,

            # TODO: Add more settings here as DB columns are added
            # Hardcoded until DB columns exist
            "auto_save_conversations": True,
            "dark_mode": True,
        }

    def __repr__(self) -> str:
        return (
            f"UserSettings(user_id={self.user_id}, provider='{self.provider}', "
            f"default_model='{self.default_model}', enable_streaming={self.enable_streaming}, "
            f"enable_extended_thinking={self.enable_extended_thinking}, "
            f"updated_at={self.updated_at})"
        )
