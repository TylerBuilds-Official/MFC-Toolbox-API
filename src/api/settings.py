from fastapi import APIRouter, HTTPException, Depends
from src.utils.settings_utils import UserSettingsService
from src.tools.auth import User, get_current_user

router = APIRouter()

@router.get("/settings")
async def get_settings(user: User = Depends(get_current_user)):
    """Get current user's settings."""
    settings = UserSettingsService.get_settings(user.id)
    return settings.to_dict()


@router.post("/settings")
async def update_settings(updates: dict, user: User = Depends(get_current_user)):
    """Bulk update user settings."""
    try:
        settings = UserSettingsService.update_settings(user.id, updates)
        return {"status": "settings updated", "settings": settings.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/settings/provider")
async def get_provider_settings(user: User = Depends(get_current_user)):
    """Get user's current provider and default model."""
    settings = UserSettingsService.get_settings(user.id)
    return {
        "provider": settings.provider,
        "default_model": settings.default_model
    }


@router.post("/settings/provider")
async def set_provider(
        provider: str,
        default_model: str = None,
        user: User = Depends(get_current_user)
):
    """Set user's provider preference (and optionally default model)."""
    try:
        settings = UserSettingsService.update_provider(user.id, provider, default_model)
        return {
            "status": "updated",
            "provider": settings.provider,
            "default_model": settings.default_model
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
