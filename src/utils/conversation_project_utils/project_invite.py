"""
ProjectInvite dataclass for pending project invitations.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class ProjectInvite:
    """Represents a pending invitation to a conversation project."""
    
    id: int
    project_id: int
    project_name: str
    project_description: Optional[str]
    project_color: Optional[str]
    project_type: str
    invited_by_name: str
    invited_by_email: str
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            'id':                  self.id,
            'project_id':          self.project_id,
            'project_name':        self.project_name,
            'project_description': self.project_description,
            'project_color':       self.project_color,
            'project_type':        self.project_type,
            'invited_by_name':     self.invited_by_name,
            'invited_by_email':    self.invited_by_email,
            'created_at':          self.created_at.isoformat() if self.created_at else None,
            'expires_at':          self.expires_at.isoformat() if self.expires_at else None,
        }

    @staticmethod
    def from_dict(data: dict) -> "ProjectInvite":
        """Create ProjectInvite from dictionary."""
        return ProjectInvite(
            id=data['id'],
            project_id=data['project_id'],
            project_name=data['project_name'],
            project_description=data.get('project_description'),
            project_color=data.get('project_color'),
            project_type=data['project_type'],
            invited_by_name=data['invited_by_name'],
            invited_by_email=data['invited_by_email'],
            created_at=data.get('created_at'),
            expires_at=data.get('expires_at'),
        )

    def __repr__(self):
        return (
            f"ProjectInvite(id={self.id}, project='{self.project_name}', "
            f"from='{self.invited_by_name}')"
        )
