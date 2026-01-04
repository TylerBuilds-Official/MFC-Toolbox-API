from fastapi import APIRouter, Depends, HTTPException
from src.tools.auth import User, require_role
from src.tools.auth.user_service import UserService


router = APIRouter()

@router.get("/admin/users")
async def list_all_users(user: User = Depends(require_role("admin"))):
    """List all users in the system."""
    users = UserService.list_users()
    return {
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "display_name": u.display_name,
                "role": u.role,
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
    """Set a user's role (admin only)."""
    user_access_level = user.role
    if user_access_level != "admin":
        return {"status": "error", "message": "You do not have permission to update user roles"}

    try:
        success = UserService.set_user_role(user_id, role)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        return {"status": "updated", "user_id": user_id, "role": role}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))