"""
ProjectMember dataclass for project membership.
"""
from dataclasses import dataclass
from typing import Optional, Literal
from datetime import datetime


@dataclass
class ProjectMember:
    """Represents a member of a conversation project."""
    
    id: int
    user_id: int
    display_name: str
    email: str
    role: Literal['owner', 'member']
    joined_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            'id':           self.id,
            'user_id':      self.user_id,
            'display_name': self.display_name,
            'email':        self.email,
            'role':         self.role,
            'joined_at':    self.joined_at.isoformat() if self.joined_at else None,
        }

    @staticmethod
    def from_dict(data: dict) -> "ProjectMember":
        """Create ProjectMember from dictionary."""
        return ProjectMember(
            id=data['id'],
            user_id=data['user_id'],
            display_name=data['display_name'],
            email=data['email'],
            role=data['role'],
            joined_at=data.get('joined_at'),
        )

    def __repr__(self):
        return (
            f"ProjectMember(user_id={self.user_id}, "
            f"name='{self.display_name}', role='{self.role}')"
        )
