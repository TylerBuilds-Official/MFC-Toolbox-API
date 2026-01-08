"""
ConversationProject dataclass for conversation project folders.
"""
from dataclasses import dataclass, field
from typing import Optional, Literal
from datetime import datetime


@dataclass
class ProjectPermissions:
    """Permissions configuration for shared_open projects."""
    
    can_chat: Literal['owner_only', 'anyone']                  = 'anyone'
    can_create_conversations: Literal['owner_only', 'anyone']  = 'anyone'
    can_edit_instructions: Literal['owner_only', 'anyone']     = 'owner_only'
    can_invite_members: Literal['owner_only', 'anyone']        = 'owner_only'
    can_remove_conversations: Literal['owner_only', 'anyone']  = 'anyone'

    def to_dict(self) -> dict:
        """Convert to dictionary for API/DB."""
        return {
            'canChat':                self.can_chat,
            'canCreateConversations': self.can_create_conversations,
            'canEditInstructions':    self.can_edit_instructions,
            'canInviteMembers':       self.can_invite_members,
            'canRemoveConversations': self.can_remove_conversations,
        }
    
    @staticmethod
    def from_dict(data: dict) -> "ProjectPermissions":
        """Create ProjectPermissions from dictionary."""
        if not data:
            return ProjectPermissions()
        return ProjectPermissions(
            can_chat=data.get('canChat', 'anyone'),
            can_create_conversations=data.get('canCreateConversations', 'anyone'),
            can_edit_instructions=data.get('canEditInstructions', 'owner_only'),
            can_invite_members=data.get('canInviteMembers', 'owner_only'),
            can_remove_conversations=data.get('canRemoveConversations', 'anyone'),
        )


# Default permissions for shared_open projects
DEFAULT_PERMISSIONS = ProjectPermissions()


@dataclass
class ConversationProject:
    """Represents a conversation project (folder for organizing conversations)."""
    
    id: int
    owner_id: int
    name: str
    project_type: Literal['private', 'shared_locked', 'shared_open'] = 'private'
    description: Optional[str] = None
    color: Optional[str] = None
    custom_instructions: Optional[str] = None
    permissions: Optional[ProjectPermissions] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True
    conversation_count: int = 0
    member_count: int = 0
    is_owner: bool = False
    user_role: Optional[str] = None  # 'owner' | 'member' | None

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            'id':                  self.id,
            'owner_id':            self.owner_id,
            'name':                self.name,
            'description':         self.description,
            'color':               self.color,
            'custom_instructions': self.custom_instructions,
            'project_type':        self.project_type,
            'permissions':         self.permissions.to_dict() if self.permissions else None,
            'created_at':          self.created_at.isoformat() if self.created_at else None,
            'updated_at':          self.updated_at.isoformat() if self.updated_at else None,
            'is_active':           self.is_active,
            'conversation_count':  self.conversation_count,
            'member_count':        self.member_count,
            'is_owner':            self.is_owner,
            'user_role':           self.user_role,
        }

    @staticmethod
    def from_dict(data: dict) -> "ConversationProject":
        """Create ConversationProject from dictionary."""
        permissions = None
        if data.get('permissions'):
            permissions = ProjectPermissions.from_dict(data['permissions'])
        
        return ConversationProject(
            id=data['id'],
            owner_id=data['owner_id'],
            name=data['name'],
            description=data.get('description'),
            color=data.get('color'),
            custom_instructions=data.get('custom_instructions'),
            project_type=data.get('project_type', 'private'),
            permissions=permissions,
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            is_active=data.get('is_active', True),
            conversation_count=data.get('conversation_count', 0),
            member_count=data.get('member_count', 0),
            is_owner=data.get('is_owner', False),
            user_role=data.get('user_role'),
        )

    def __repr__(self):
        return (
            f"ConversationProject(id={self.id}, name='{self.name}', "
            f"type='{self.project_type}', conversations={self.conversation_count})"
        )
