"""
API endpoints for conversation projects (project folders for organizing conversations).

IMPORTANT: Route order matters in FastAPI!
Static paths (like /invites) must come BEFORE parameterized paths (like /{project_id})
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, Literal

from src.utils.conversation_project_utils import (
    ConversationProjectService,
    ProjectPermissions,
)
from src.tools.auth import User, require_active_user


router = APIRouter()


# ============================================================================
# Request Models
# ============================================================================

class PermissionsRequest(BaseModel):
    """Permissions configuration for shared_open projects."""
    canChat: Literal['owner_only', 'anyone']                 = 'anyone'
    canCreateConversations: Literal['owner_only', 'anyone']  = 'anyone'
    canEditInstructions: Literal['owner_only', 'anyone']     = 'owner_only'
    canInviteMembers: Literal['owner_only', 'anyone']        = 'owner_only'
    canRemoveConversations: Literal['owner_only', 'anyone']  = 'anyone'


class CreateProjectRequest(BaseModel):
    """Request body for creating a project."""
    name: str
    description: Optional[str]                                        = None
    color: Optional[str]                                              = None
    custom_instructions: Optional[str]                                = None
    project_type: Literal['private', 'shared_locked', 'shared_open']  = 'private'
    permissions: Optional[PermissionsRequest]                         = None


class UpdateProjectRequest(BaseModel):
    """Request body for updating a project."""
    name: Optional[str]                                               = None
    description: Optional[str]                                        = None
    color: Optional[str]                                              = None
    custom_instructions: Optional[str]                                = None
    project_type: Optional[Literal['private', 'shared_locked', 'shared_open']] = None
    permissions: Optional[PermissionsRequest]                         = None


class DeleteProjectRequest(BaseModel):
    """Request body for deleting a project."""
    delete_conversations: bool = False


class AddConversationRequest(BaseModel):
    """Request body for adding a conversation to a project."""
    project_id: int


class SetConversationProjectsRequest(BaseModel):
    """Request body for setting all projects for a conversation."""
    project_ids: list[int]


class InviteRequest(BaseModel):
    """Request body for inviting a user to a project."""
    email: EmailStr
    expires_in_days: int = 7


# ============================================================================
# Helper Functions
# ============================================================================

def permissions_request_to_model(req: PermissionsRequest) -> ProjectPermissions:
    """Convert API request to ProjectPermissions model."""
    return ProjectPermissions(
        can_chat=req.canChat,
        can_create_conversations=req.canCreateConversations,
        can_edit_instructions=req.canEditInstructions,
        can_invite_members=req.canInviteMembers,
        can_remove_conversations=req.canRemoveConversations,
    )


# ============================================================================
# Project List & Create (no path params)
# ============================================================================

@router.get("/conversations/projects")
async def list_projects(user: User = Depends(require_active_user)):
    """
    List all conversation projects for the current user.
    
    Returns projects owned by user and projects shared with user.
    Owned projects appear first, then shared projects.
    """
    projects = ConversationProjectService.list_projects(user.id)
    
    # Separate owned and shared for frontend convenience
    owned = [p.to_dict() for p in projects if p.is_owner]
    shared = [p.to_dict() for p in projects if not p.is_owner]
    
    return {
        "projects": [p.to_dict() for p in projects],
        "owned": owned,
        "shared": shared,
        "count": len(projects)
    }


@router.post("/conversations/projects")
async def create_project(
    body: CreateProjectRequest,
    user: User = Depends(require_active_user)
):
    """
    Create a new conversation project.
    
    Projects act as folders to organize conversations.
    Types: private (only you), shared_locked (view only), shared_open (collaborative).
    """
    permissions = None
    if body.permissions:
        permissions = permissions_request_to_model(body.permissions)
    
    project = ConversationProjectService.create_project(
        owner_id=user.id,
        name=body.name,
        description=body.description,
        color=body.color,
        custom_instructions=body.custom_instructions,
        project_type=body.project_type,
        permissions=permissions
    )
    return project.to_dict()


# ============================================================================
# Invite Endpoints (MUST come before /{project_id} routes!)
# ============================================================================

@router.get("/conversations/projects/invites")
async def get_pending_invites(user: User = Depends(require_active_user)):
    """
    Get all pending project invites for the current user.
    
    Returns invites that haven't been accepted, declined, or expired.
    """
    invites = ConversationProjectService.get_invites(user.email)
    return {
        "invites": [i.to_dict() for i in invites],
        "count": len(invites)
    }


# ============================================================================
# Community (Open Projects) - MUST come before /{project_id} routes!
# ============================================================================

@router.get("/conversations/projects/community")
async def list_community_projects(user: User = Depends(require_active_user)):
    """
    List all shared_open projects the user hasn't joined yet.
    
    These are discoverable projects anyone can join without an invite.
    """
    projects = ConversationProjectService.list_community_projects(user.id)
    return {
        "projects": projects,
        "count": len(projects)
    }


@router.post("/conversations/projects/invites/{invite_id}/accept")
async def accept_invite(
    invite_id: int,
    user: User = Depends(require_active_user)
):
    """
    Accept a project invite.
    
    User will be added as a member of the project.
    """
    try:
        result = ConversationProjectService.accept_invite(
            invite_id, user.id, user.email
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return result


@router.post("/conversations/projects/invites/{invite_id}/decline")
async def decline_invite(
    invite_id: int,
    user: User = Depends(require_active_user)
):
    """
    Decline a project invite.
    """
    try:
        success = ConversationProjectService.decline_invite(invite_id, user.email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to decline invite")
    
    return {"success": True, "message": "Invite declined"}


# ============================================================================
# Project CRUD with {project_id} (after static paths)
# ============================================================================

@router.get("/conversations/projects/{project_id}")
async def get_project(
    project_id: int,
    user: User = Depends(require_active_user)
):
    """Get a specific project by ID."""
    project = ConversationProjectService.get_project(project_id, user.id)
    
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project.to_dict()


@router.patch("/conversations/projects/{project_id}")
async def update_project(
    project_id: int,
    body: UpdateProjectRequest,
    user: User = Depends(require_active_user)
):
    """
    Update a conversation project.
    
    All fields are optional. Only provided fields will be updated.
    To clear description, color, or custom_instructions, send an empty string.
    """
    # Check if any updates were provided
    if all(v is None for v in [
        body.name, body.description, body.color,
        body.custom_instructions, body.project_type, body.permissions
    ]):
        raise HTTPException(status_code=400, detail="No updates provided")
    
    permissions = None
    if body.permissions is not None:
        permissions = permissions_request_to_model(body.permissions)
    
    try:
        project = ConversationProjectService.update_project(
            project_id=project_id,
            user_id=user.id,
            name=body.name,
            description=body.description,
            color=body.color,
            custom_instructions=body.custom_instructions,
            project_type=body.project_type,
            permissions=permissions
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project.to_dict()


@router.delete("/conversations/projects/{project_id}")
async def delete_project(
    project_id: int,
    body: DeleteProjectRequest = None,
    user: User = Depends(require_active_user)
):
    """
    Delete a conversation project.
    
    Only the owner can delete a project.
    If delete_conversations is True, conversations that are ONLY in this project
    (not in any other projects) will also be deleted.
    """
    delete_convos = body.delete_conversations if body else False
    
    try:
        success = ConversationProjectService.delete_project(
            project_id, user.id, delete_convos
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {"success": True, "message": "Project deleted"}


# ============================================================================
# Project sub-resources: /conversations, /members, /invite
# ============================================================================

@router.get("/conversations/projects/{project_id}/conversations")
async def get_project_conversations(
    project_id: int,
    user: User = Depends(require_active_user)
):
    """
    Get all conversations in a project.
    
    Returns conversations with their project membership info.
    """
    try:
        conversations = ConversationProjectService.get_conversations_in_project(
            project_id, user.id
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    
    return {
        "conversations": conversations,
        "count": len(conversations)
    }


@router.post("/conversations/projects/{project_id}/invite")
async def invite_to_project(
    project_id: int,
    body: InviteRequest,
    user: User = Depends(require_active_user)
):
    """
    Invite a user to a project by email.
    
    Only works for shared_locked and shared_open projects.
    User must accept the invite to join.
    """
    try:
        result = ConversationProjectService.invite_user(
            project_id=project_id,
            invited_email=body.email,
            invited_by=user.id,
            expires_in_days=body.expires_in_days
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return result


@router.get("/conversations/projects/{project_id}/members")
async def get_project_members(
    project_id: int,
    user: User = Depends(require_active_user)
):
    """
    Get all members of a project.
    
    Owner is listed first.
    """
    try:
        members = ConversationProjectService.get_members(project_id, user.id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    
    return {
        "members": [m.to_dict() for m in members],
        "count": len(members)
    }


@router.delete("/conversations/projects/{project_id}/members/{member_user_id}")
async def remove_project_member(
    project_id: int,
    member_user_id: int,
    user: User = Depends(require_active_user)
):
    """
    Remove a member from a project.
    
    Only the owner can remove members.
    A member can remove themselves (leave the project).
    Cannot remove the owner.
    """
    try:
        success = ConversationProjectService.remove_member(
            project_id, member_user_id, user.id
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to remove member")
    
    return {"success": True, "message": "Member removed"}


@router.get("/conversations/projects/{project_id}/invites")
async def get_project_invites(
    project_id: int,
    user: User = Depends(require_active_user)
):
    """
    Get all invites for a project (owner view).
    
    Returns pending, declined, and expired invites.
    Only the project owner can view this.
    """
    try:
        invites = ConversationProjectService.get_invites_for_project(project_id, user.id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    
    return {
        "invites": invites,
        "count": len(invites)
    }


@router.delete("/conversations/projects/{project_id}/invites/{invite_id}")
async def cancel_project_invite(
    project_id: int,
    invite_id: int,
    user: User = Depends(require_active_user)
):
    """
    Cancel a pending project invite.
    
    Only the project owner can cancel invites.
    Only pending invites can be cancelled.
    """
    try:
        success = ConversationProjectService.cancel_invite(invite_id, user.id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to cancel invite")
    
    return {"success": True, "message": "Invite cancelled"}


@router.post("/conversations/projects/{project_id}/join")
async def join_open_project(
    project_id: int,
    user: User = Depends(require_active_user)
):
    """
    Join a shared_open project directly (no invite required).
    
    Only works for shared_open projects. User will be added as a member.
    """
    try:
        result = ConversationProjectService.join_project(project_id, user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', 'Failed to join project'))
    
    return result


# ============================================================================
# Conversation <-> Project Membership (different base path)
# ============================================================================

@router.post("/conversations/{conversation_id}/projects")
async def add_conversation_to_project(
    conversation_id: int,
    body: AddConversationRequest,
    user: User = Depends(require_active_user)
):
    """
    Add a conversation to a project.
    
    A conversation can belong to multiple projects.
    """
    try:
        result = ConversationProjectService.add_conversation(
            conversation_id, body.project_id, user.id
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return result


@router.put("/conversations/{conversation_id}/projects")
async def set_conversation_projects(
    conversation_id: int,
    body: SetConversationProjectsRequest,
    user: User = Depends(require_active_user)
):
    """
    Set all projects for a conversation (sync).
    
    Removes conversation from projects not in the list,
    adds conversation to projects in the list.
    """
    try:
        result = ConversationProjectService.sync_conversation_projects(
            conversation_id, body.project_ids, user.id
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return result


@router.delete("/conversations/{conversation_id}/projects/{project_id}")
async def remove_conversation_from_project(
    conversation_id: int,
    project_id: int,
    user: User = Depends(require_active_user)
):
    """
    Remove a conversation from a project.
    
    The conversation is not deleted, just unlinked from the project.
    """
    try:
        success = ConversationProjectService.remove_conversation(
            conversation_id, project_id, user.id
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to remove conversation")
    
    return {"success": True, "message": "Conversation removed from project"}


@router.get("/conversations/{conversation_id}/projects")
async def get_conversation_projects(
    conversation_id: int,
    user: User = Depends(require_active_user)
):
    """
    Get all projects a conversation belongs to.
    
    Useful for showing project badges/tags on conversation items.
    """
    try:
        projects = ConversationProjectService.get_projects_for_conversation(
            conversation_id, user.id
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    
    return {
        "projects": projects,
        "count": len(projects)
    }
