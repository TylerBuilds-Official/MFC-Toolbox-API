# src/tools/auth/__init__.py
"""
Authentication and authorization for MFC Toolbox.
Uses Azure AD for identity and MS SQL for user/role persistence.
"""
from src.tools.auth.user_service import UserService, User
from src.tools.auth.dependencies import get_current_user, require_role, require_active_user

__all__ = [
    "UserService",
    "User",
    "get_current_user",
    "require_role",
    "require_active_user"
]
