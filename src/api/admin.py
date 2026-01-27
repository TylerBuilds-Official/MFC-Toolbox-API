from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from src.tools.auth import User, require_role
from src.tools.auth.user_service import UserService
from src.utils.admin_utils import (
    AdminStatsService,
    AdminUserActivityService,
    AdminConversationService,
    AdminMemoryService,
    AdminToolStatsService,
    AdminAuditService,
    AdminHealthService,
)


router = APIRouter()


# =============================================================================
# User Management
# =============================================================================

@router.get("/admin/users")
async def list_all_users(user: User = Depends(require_role("admin"))):
    """List all users in the system with their specialties."""
    users = UserService.list_users()
    return {
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "display_name": u.display_name,
                "role": u.role,
                "specialty_roles": u.specialty_roles,
                "created_at": u.created_at.isoformat(),
                "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
            }
            for u in users
        ]
    }


@router.post("/admin/users/{user_id}/role")
async def set_user_role(
        user_id: int,
        role: str,
        user: User = Depends(require_role("admin"))
):
    """Set a user's base role (admin only)."""
    # Get target user info for audit
    target_user = UserService.get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    old_role = target_user.role
    
    try:
        success = UserService.set_user_role(user_id, role)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Log the action
        AdminAuditService.log_action(
            action="role_change",
            actor_id=user.id,
            actor_name=user.display_name,
            target_type="user",
            target_id=user_id,
            target_name=target_user.display_name,
            details={"old_role": old_role, "new_role": role},
        )
        
        return {"status": "updated", "user_id": user_id, "role": role}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Specialty Management
# =============================================================================

@router.get("/admin/specialties")
async def list_valid_specialties(user: User = Depends(require_role("admin"))):
    """List all valid specialty roles that can be assigned."""
    return {
        "specialties": list(UserService.VALID_SPECIALTIES),
        "count": len(UserService.VALID_SPECIALTIES)
    }


@router.get("/admin/users/{user_id}/specialties")
async def get_user_specialties(
        user_id: int,
        user: User = Depends(require_role("admin"))
):
    """Get all specialties for a specific user with audit info."""
    target_user = UserService.get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    specialties = UserService.get_user_specialties(user_id)
    return {
        "user_id": user_id,
        "user_name": target_user.display_name,
        "specialties": specialties,
        "count": len(specialties)
    }


@router.post("/admin/users/{user_id}/specialties")
async def grant_user_specialty(
        user_id: int,
        specialty: str,
        user: User = Depends(require_role("admin"))
):
    """Grant a specialty role to a user."""
    try:
        # Get target user info for audit
        target_user = UserService.get_user_by_id(user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        success = UserService.grant_specialty(user_id, specialty, granted_by=user.id)
        if not success:
            raise HTTPException(status_code=409, detail="User already has this specialty")
        
        # Log the action
        AdminAuditService.log_action(
            action="specialty_grant",
            actor_id=user.id,
            actor_name=user.display_name,
            target_type="user",
            target_id=user_id,
            target_name=target_user.display_name,
            details={"specialty": specialty},
        )
        
        return {
            "status": "granted",
            "user_id": user_id,
            "specialty": specialty,
            "granted_by": user.id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/admin/users/{user_id}/specialties/{specialty}")
async def revoke_user_specialty(
        user_id: int,
        specialty: str,
        user: User = Depends(require_role("admin"))
):
    """Revoke a specialty role from a user."""
    # Get target user info for audit
    target_user = UserService.get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    success = UserService.revoke_specialty(user_id, specialty)
    if not success:
        raise HTTPException(status_code=404, detail="User does not have this specialty")
    
    # Log the action
    AdminAuditService.log_action(
        action="specialty_revoke",
        actor_id=user.id,
        actor_name=user.display_name,
        target_type="user",
        target_id=user_id,
        target_name=target_user.display_name,
        details={"specialty": specialty},
    )
    
    return {
        "status": "revoked",
        "user_id": user_id,
        "specialty": specialty
    }


@router.get("/admin/specialties/{specialty}/users")
async def get_users_by_specialty(
        specialty: str,
        user: User = Depends(require_role("admin"))
):
    """Get all users who have a specific specialty."""
    if specialty not in UserService.VALID_SPECIALTIES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid specialty '{specialty}'. Must be one of: {list(UserService.VALID_SPECIALTIES)}"
        )
    
    users = UserService.get_users_by_specialty(specialty)
    return {
        "specialty": specialty,
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "display_name": u.display_name,
                "role": u.role,
            }
            for u in users
        ],
        "count": len(users)
    }


# =============================================================================
# Dashboard Stats (P0)
# =============================================================================

@router.get("/admin/stats")
async def get_dashboard_stats(user: User = Depends(require_role("admin"))):
    """
    Get comprehensive dashboard statistics.
    
    Returns aggregated metrics for:
    - Users (total, by role, active today/this week)
    - Conversations (total, active, this week)
    - Messages (total, this week)
    - Memories (total, by type)
    - Data Sessions (total, by status)
    """
    stats = AdminStatsService.get_dashboard_stats()
    return stats


# =============================================================================
# User Activity (P0)
# =============================================================================

@router.get("/admin/users/{user_id}/activity")
async def get_user_activity(
        user_id: int,
        user: User = Depends(require_role("admin"))
):
    """
    Get detailed activity stats for a specific user.
    
    Returns:
    - Basic user info
    - Conversation, message, memory, data session counts
    - Last conversation timestamp
    - 10 most recent conversations
    """
    activity = AdminUserActivityService.get_user_activity(user_id)
    
    if activity is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return activity


# =============================================================================
# Cross-User Conversations (P1)
# =============================================================================

@router.get("/admin/conversations")
async def list_all_conversations(
        limit: int = Query(default=50, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        user_id: Optional[int] = Query(default=None),
        include_inactive: bool = Query(default=False),
        user: User = Depends(require_role("admin"))
):
    """
    List conversations across all users (admin view).
    
    Query params:
    - limit: Max results (1-100, default 50)
    - offset: Pagination offset
    - user_id: Filter by specific user
    - include_inactive: Include soft-deleted conversations
    """
    result = AdminConversationService.list_all_conversations(
        limit=limit,
        offset=offset,
        user_id=user_id,
        include_inactive=include_inactive,
    )
    return result


# =============================================================================
# Cross-User Memories (P1)
# =============================================================================

@router.get("/admin/memories")
async def list_all_memories(
        limit: int = Query(default=50, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        user_id: Optional[int] = Query(default=None),
        memory_type: Optional[str] = Query(default=None),
        include_inactive: bool = Query(default=False),
        user: User = Depends(require_role("admin"))
):
    """
    List memories across all users (admin view).
    
    Query params:
    - limit: Max results (1-100, default 50)
    - offset: Pagination offset
    - user_id: Filter by specific user
    - memory_type: Filter by type (fact, preference, project, skill, context)
    - include_inactive: Include soft-deleted memories
    """
    # Validate memory_type if provided
    valid_types = {'fact', 'preference', 'project', 'skill', 'context'}
    if memory_type is not None and memory_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid memory_type '{memory_type}'. Must be one of: {valid_types}"
        )
    
    result = AdminMemoryService.list_all_memories(
        limit=limit,
        offset=offset,
        user_id=user_id,
        memory_type=memory_type,
        include_inactive=include_inactive,
    )
    return result


# =============================================================================
# Tool Usage Stats (P2)
# =============================================================================

@router.get("/admin/tools/stats")
async def get_tool_stats(user: User = Depends(require_role("admin"))):
    """
    Get usage statistics for all tools.
    
    Returns:
    - Per-tool metrics (executions, success rate, last used, unique users)
    - Daily trend for the past week
    """
    stats = AdminToolStatsService.get_tool_stats()
    return stats


# =============================================================================
# Audit Log (P2)
# =============================================================================

@router.get("/admin/audit")
async def get_audit_log(
        limit: int = Query(default=50, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        action_type: Optional[str] = Query(default=None),
        actor_id: Optional[int] = Query(default=None),
        target_type: Optional[str] = Query(default=None),
        user: User = Depends(require_role("admin"))
):
    """
    Get admin audit log entries.
    
    Query params:
    - limit: Max results (1-100, default 50)
    - offset: Pagination offset
    - action_type: Filter by action (e.g., 'role_change', 'specialty_grant')
    - actor_id: Filter by admin who performed action
    - target_type: Filter by target type ('user', 'conversation', etc.)
    """
    result = AdminAuditService.get_audit_log(
        limit=limit,
        offset=offset,
        action_type=action_type,
        actor_id=actor_id,
        target_type=target_type,
    )
    return result


@router.get("/admin/audit/actions")
async def get_audit_action_types(user: User = Depends(require_role("admin"))):
    """Get list of all action types that have been logged."""
    action_types = AdminAuditService.get_action_types()
    return {
        "action_types": action_types,
        "count": len(action_types),
    }


# =============================================================================
# Extended Health Check (P3)
# =============================================================================

@router.get("/admin/health")
async def get_health_status(user: User = Depends(require_role("admin"))):
    """
    Get extended health status for admin dashboard.
    
    Returns:
    - Overall status (healthy/degraded)
    - Database connectivity and latency
    - Connected agents info
    - Server uptime
    """
    health = AdminHealthService.get_health_status()
    return health