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

    def to_dict(self) -> dict:
        """Convert to API response format."""
        return {
            "provider": self.provider,
            "default_model": self.default_model,

            # TODO ADD MORE SETTINGS HERE
            # Hardcoded until DB columns are added
            "auto_save_conversations": True,
            "dark_mode": True,
        }

    def __repr__(self) -> str:
        return f"UserSettings(user_id={self.user_id}, provider='{self.provider}', default_model='{self.default_model}', updated_at={self.updated_at})"
