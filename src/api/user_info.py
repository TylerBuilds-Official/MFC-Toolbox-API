from fastapi import Depends, APIRouter
from src.tools.auth import User, get_current_user

router = APIRouter()

@router.get("/me")
async def get_current_user_info(user: User = Depends(get_current_user)):
    """Get current user's profile information."""
    print(f"[/me] Returning user info for: {user.email}")
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role,
        "is_active": user.is_active,
    }
