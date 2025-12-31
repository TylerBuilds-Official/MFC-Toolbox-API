from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Memory:
    """Represents a user memory."""
    id: int
    user_id: int
    memory_type: str
    content: str
    source_conversation_id: Optional[int]
    source_message_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    is_active: bool

    def to_dict(self) -> dict:
        """Convert to API response format."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "memory_type": self.memory_type,
            "content": self.content,
            "source_conversation_id": self.source_conversation_id,
            "source_message_id": self.source_message_id,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
            "is_active": self.is_active,
        }

    def __repr__(self) -> str:
        return (
            f"Memory(id={self.id}, user_id={self.user_id}, "
            f"type='{self.memory_type}', content='{self.content[:50]}...')"
        )
