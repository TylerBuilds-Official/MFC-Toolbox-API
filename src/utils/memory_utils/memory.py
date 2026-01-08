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
    # New tracking fields
    last_referenced_at: Optional[datetime] = None
    reference_count: int = 0
    expires_at: Optional[datetime] = None

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
            "last_referenced_at": self.last_referenced_at.isoformat() if isinstance(self.last_referenced_at, datetime) else self.last_referenced_at,
            "reference_count": self.reference_count,
            "expires_at": self.expires_at.isoformat() if isinstance(self.expires_at, datetime) else self.expires_at,
            "is_stale": self.is_stale,
            "is_expired": self.is_expired,
        }

    @property
    def is_stale(self) -> bool:
        """Check if memory hasn't been referenced in 90 days."""
        days = 90
        if self.last_referenced_at is None:
            # Never referenced - check created_at instead
            age = (datetime.now() - self.created_at).days if self.created_at else 0
            return age > days
        age = (datetime.now() - self.last_referenced_at).days
        return age > days

    def is_stale_days(self, days: int = 90) -> bool:
        """Check if memory hasn't been referenced in X days."""
        if self.last_referenced_at is None:
            # Never referenced - check created_at instead
            age = (datetime.now() - self.created_at).days if self.created_at else 0
            return age > days
        age = (datetime.now() - self.last_referenced_at).days
        return age > days

    @property
    def is_expired(self) -> bool:
        """Check if memory has passed its expiration date."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def __repr__(self) -> str:
        return (
            f"Memory(id={self.id}, user_id={self.user_id}, "
            f"type='{self.memory_type}', refs={self.reference_count}, "
            f"content='{self.content[:50]}...')"
        )
