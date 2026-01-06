"""
DataGroup dataclass for data session groups.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class DataGroup:
    """Represents a user's data session group (project folder)."""
    
    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    session_count: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "session_count": self.session_count,
        }

    @staticmethod
    def from_dict(data: dict) -> "DataGroup":
        """Create DataGroup from dictionary."""
        return DataGroup(
            id=data['id'],
            user_id=data['user_id'],
            name=data['name'],
            description=data.get('description'),
            color=data.get('color'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            session_count=data.get('session_count', 0),
        )

    def __repr__(self):
        return (
            f"DataGroup(id={self.id}, name='{self.name}', "
            f"session_count={self.session_count})"
        )
