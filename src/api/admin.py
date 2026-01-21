from fastapi import APIRouter, Depends, HTTPException
from src.tools.auth import User, require_role
from src.tools.auth.user_service import UserService


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
    try:
        success = UserService.set_user_role(user_id, role)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
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
        success = UserService.grant_specialty(user_id, specialty, granted_by=user.id)
        if not success:
            # Could be user not found or already has specialty
            target_user = UserService.get_user_by_id(user_id)
            if not target_user:
                raise HTTPException(status_code=404, detail="User not found")
            else:
                raise HTTPException(status_code=409, detail="User already has this specialty")
        
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
    success = UserService.revoke_specialty(user_id, specialty)
    if not success:
        raise HTTPException(status_code=404, detail="User does not have this specialty")
    
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