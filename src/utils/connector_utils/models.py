from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# Schema constant for toolbox_agents
AGENTS_SCHEMA = "toolbox_agents"


class RegisteredAgent(BaseModel):
    """Persisted agent registration."""
    id: Optional[int] = None
    user_id: str
    username: str
    hostname: str
    agent_version: Optional[str] = None
    first_registered_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None


class ConnectorConfig(BaseModel):
    """User's connector configuration."""
    id: Optional[int] = None
    user_id: str
    connector_type: str
    enabled: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AllowedFolder(BaseModel):
    """User's allowed folder with permissions."""
    id: Optional[int] = None
    user_id: str
    path: str
    can_read: bool = True
    can_write: bool = False
    can_delete: bool = False
    created_at: Optional[datetime] = None


class AllowedFolderCreate(BaseModel):
    """Request model for adding a folder."""
    path: str
    can_read: bool = True
    can_write: bool = False
    can_delete: bool = False


class AllowedFolderUpdate(BaseModel):
    """Request model for updating folder permissions."""
    can_read: Optional[bool] = None
    can_write: Optional[bool] = None
    can_delete: Optional[bool] = None


class ConnectorStatus(BaseModel):
    """Full status of a connector for a user."""
    connector_type: str
    enabled: bool
    agent_connected: bool
    agent_hostname: Optional[str] = None
    agent_version: Optional[str] = None
    folders: list[AllowedFolder] = []
