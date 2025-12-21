# src/tools/auth/dependencies.py
"""
FastAPI dependencies for authentication and authorization.
Use these to protect routes and inject the current user.
"""
from typing import Callable
from fastapi import Depends, HTTPException, status
from src.tools.auth.azure_auth import azure_scheme
from src.tools.auth.user_service import UserService, User


async def get_current_user(token: dict = Depends(azure_scheme)) -> User:
    """
    FastAPI dependency that validates Azure AD token and returns User object.
    Creates user record on first sign-in.
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            return {"message": f"Hello {user.display_name}"}
    """


    print(f"[AUTH] Token claims received: {token}")
    
    azure_oid = token.get("oid")
    email = token.get("preferred_username") or token.get("email") or token.get("upn", "")
    display_name = token.get("name", "")
    
    print(f"[AUTH] Extracted - OID: {azure_oid}, Email: {email}, Name: {display_name}")
    
    if not azure_oid:
        print("[AUTH] Missing OID in token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing object ID",
            headers={"WWW-Authenticate": "Bearer"})
    
    print(f"[AUTH] Creating/fetching user for OID: {azure_oid}")
    user = UserService.get_or_create_user(azure_oid, email, display_name)
    print(f"[AUTH] User authenticated: {user.email} (Role: {user.role})")
    return user


def require_role(*allowed_roles: str) -> Callable:
    """
    Dependency factory for role-based access control.
    
    Usage:
        @app.get("/admin/users")
        async def list_users(user: User = Depends(require_role("admin"))):
            return UserService.list_users()
        
        @app.get("/dashboard")
        async def dashboard(user: User = Depends(require_role("user", "admin"))):
            return {"message": "Welcome!"}
    """

    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {allowed_roles}, your role: {user.role}")
        return user

    return role_checker


def require_active_user(user: User = Depends(get_current_user)) -> User:
    """
    Dependency that requires user to be activated (not 'pending').
    
    Usage:
        @app.get("/chat")
        async def chat(user: User = Depends(require_active_user)):
            ...
    """
    print(f"[AUTH] Checking user activation status: {user.email} (Role: {user.role})")
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account pending activation. Please contact an administrator.")
    return user
