"""
API endpoints for data session groups (project folders).
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from src.utils.data_utils import DataGroupService
from src.tools.auth import User, require_active_user


router = APIRouter()


# ============================================
# Request Models
# ============================================

class CreateGroupRequest(BaseModel):
    """Request body for creating a group."""
    name: str
    description: Optional[str] = None
    color: Optional[str] = None


class UpdateGroupRequest(BaseModel):
    """Request body for updating a group."""
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None


class AssignSessionRequest(BaseModel):
    """Request body for assigning a session to a group."""
    group_id: int


# ============================================
# Group CRUD Endpoints
# ============================================

@router.get("/data/groups")
async def list_groups(user: User = Depends(require_active_user)):
    """
    List all data session groups for the current user.
    
    Returns groups with session counts, ordered by most recently updated.
    """
    groups = DataGroupService.list_groups(user.id)
    return {
        "groups": [g.to_dict() for g in groups],
        "count": len(groups)
    }


@router.post("/data/groups")
async def create_group(
    body: CreateGroupRequest,
    user: User = Depends(require_active_user)
):
    """
    Create a new data session group.
    
    Groups act as project folders to organize data sessions.
    """
    group = DataGroupService.create_group(
        user_id=user.id,
        name=body.name,
        description=body.description,
        color=body.color
    )
    return group.to_dict()


@router.get("/data/groups/{group_id}")
async def get_group(
    group_id: int,
    user: User = Depends(require_active_user)
):
    """Get a specific group by ID."""
    group = DataGroupService.get_group(group_id, user.id)
    
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    
    return group.to_dict()


@router.patch("/data/groups/{group_id}")
async def update_group(
    group_id: int,
    body: UpdateGroupRequest,
    user: User = Depends(require_active_user)
):
    """
    Update a data session group.
    
    All fields are optional. Only provided fields will be updated.
    To clear description or color, send an empty string.
    """
    # Check if any updates were provided
    if body.name is None and body.description is None and body.color is None:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    group = DataGroupService.update_group(
        group_id=group_id,
        user_id=user.id,
        name=body.name,
        description=body.description,
        color=body.color
    )
    
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    
    return group.to_dict()


@router.delete("/data/groups/{group_id}")
async def delete_group(
    group_id: int,
    user: User = Depends(require_active_user)
):
    """
    Delete a data session group.
    
    Sessions in the group are unlinked (moved to ungrouped), not deleted.
    """
    success = DataGroupService.delete_group(group_id, user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Group not found")
    
    return {"success": True, "message": "Group deleted"}


# ============================================
# Session Assignment Endpoints
# ============================================

@router.post("/data/sessions/{session_id}/group")
async def assign_session_to_group(
    session_id: int,
    body: AssignSessionRequest,
    user: User = Depends(require_active_user)
):
    """
    Assign a data session to a group.
    
    Moves the session from its current group (if any) to the specified group.
    """
    success = DataGroupService.add_session(session_id, body.group_id, user.id)
    
    if not success:
        raise HTTPException(
            status_code=400, 
            detail="Failed to assign session to group. Check that both exist and you own them."
        )
    
    return {"success": True, "message": "Session assigned to group"}


@router.delete("/data/sessions/{session_id}/group")
async def remove_session_from_group(
    session_id: int,
    user: User = Depends(require_active_user)
):
    """
    Remove a data session from its current group.
    
    The session becomes ungrouped but is not deleted.
    """
    success = DataGroupService.remove_session(session_id, user.id)
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Failed to remove session from group. Check that the session exists and you own it."
        )
    
    return {"success": True, "message": "Session removed from group"}
