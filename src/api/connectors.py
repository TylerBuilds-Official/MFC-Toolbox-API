"""
API endpoints for connector configuration.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from src.tools.auth import User, get_current_user
from src.utils.agent_utils import agent_registry
from src.utils.connector_utils import (
    ConnectorConfig,
    AllowedFolder,
    AllowedFolderCreate,
    AllowedFolderUpdate,
    ConnectorStatus,
    get_or_create_connector_config,
    update_connector_enabled,
    get_allowed_folders,
    get_allowed_folder_by_id,
    add_allowed_folder,
    update_allowed_folder,
    delete_allowed_folder
)

router = APIRouter(prefix="/settings/connectors")


class EnableRequest(BaseModel):
    enabled: bool


def _get_username_from_email(email: str) -> str:
    """Extract Windows username from email (e.g., 'tylere@metalsfab.com' -> 'tylere')"""
    return email.split("@")[0].lower()


# ============================================
# Connector Status
# ============================================

@router.get("/filesystem", response_model=ConnectorStatus)
async def get_filesystem_connector_status(user: User = Depends(get_current_user)):
    """Get full status of filesystem connector including agent status and folders."""
    user_id = str(user.id)
    username = _get_username_from_email(user.email)
    
    # Get config (creates with defaults if not exists)
    config = get_or_create_connector_config(user_id, "filesystem")
    
    # Check agent connection
    agent = agent_registry.get_agent(username)
    
    # Get folders
    folders = get_allowed_folders(user_id)
    
    return ConnectorStatus(
        connector_type="filesystem",
        enabled=config.enabled,
        agent_connected=agent is not None,
        agent_hostname=agent.hostname if agent else None,
        agent_version=agent.version if agent else None,
        folders=folders
    )


@router.put("/filesystem", response_model=ConnectorConfig)
async def update_filesystem_connector(
    request: EnableRequest,
    user: User = Depends(get_current_user)
):
    """Enable or disable the filesystem connector."""
    user_id = str(user.id)
    return update_connector_enabled(user_id, "filesystem", request.enabled)


# ============================================
# Folder Management
# ============================================

@router.get("/filesystem/folders", response_model=list[AllowedFolder])
async def list_allowed_folders(user: User = Depends(get_current_user)):
    """List all allowed folders for the current user."""
    user_id = str(user.id)
    return get_allowed_folders(user_id)


@router.post("/filesystem/folders", response_model=AllowedFolder)
async def create_allowed_folder(
    request: AllowedFolderCreate,
    user: User = Depends(get_current_user)
):
    """Add a new allowed folder."""
    user_id = str(user.id)
    
    # Check if folder already exists
    existing = get_allowed_folders(user_id)
    normalized_path = request.path.rstrip("\\/").lower()
    
    for folder in existing:
        if folder.path.lower() == normalized_path:
            raise HTTPException(
                status_code=409,
                detail=f"Folder already allowed: {request.path}"
            )
    
    return add_allowed_folder(
        user_id=user_id,
        path=request.path,
        can_read=request.can_read,
        can_write=request.can_write,
        can_delete=request.can_delete
    )


@router.put("/filesystem/folders/{folder_id}", response_model=AllowedFolder)
async def update_folder_permissions(
    folder_id: int,
    request: AllowedFolderUpdate,
    user: User = Depends(get_current_user)
):
    """Update permissions for an allowed folder."""
    user_id = str(user.id)
    
    # Verify ownership
    folder = get_allowed_folder_by_id(folder_id)
    
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    if folder.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    updated = update_allowed_folder(
        folder_id=folder_id,
        can_read=request.can_read,
        can_write=request.can_write,
        can_delete=request.can_delete
    )
    
    return updated


@router.delete("/filesystem/folders/{folder_id}")
async def remove_allowed_folder(
    folder_id: int,
    user: User = Depends(get_current_user)
):
    """Remove an allowed folder."""
    user_id = str(user.id)
    
    deleted = delete_allowed_folder(folder_id, user_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    return {"deleted": True, "folder_id": folder_id}


# ============================================
# Native Folder Picker
# ============================================

class FolderPickerResponse(BaseModel):
    path: Optional[str] = None
    cancelled: bool = False
    error: Optional[str] = None


@router.post("/filesystem/pick-folder", response_model=FolderPickerResponse)
async def pick_folder(
    user: User = Depends(get_current_user)
):
    """
    Open a native folder picker dialog on the user's machine.
    Returns the selected path or indicates if cancelled.
    """
    username = _get_username_from_email(user.email)
    
    # Check if agent is connected
    agent = agent_registry.get_agent(username)
    if not agent:
        raise HTTPException(
            status_code=503,
            detail="Agent not connected. Please ensure the Toolbox Agent is running on your computer."
        )
    
    try:
        result = await agent_registry.send_command(
            username=username,
            module="ui",
            action="pick_folder",
            params={"title": "Select Folder to Allow Access"},
            timeout=120.0  # Long timeout for user interaction
        )
        
        if not result.get("success"):
            return FolderPickerResponse(
                error=result.get("error", "Unknown error")
            )
        
        return FolderPickerResponse(
            path=result.get("path"),
            cancelled=result.get("cancelled", False)
        )
        
    except TimeoutError:
        return FolderPickerResponse(
            error="Folder picker timed out. Please try again."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
