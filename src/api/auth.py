import os
from fastapi import APIRouter

router = APIRouter()

@router.get("/auth/debug")
async def debug_auth():
    """Debug endpoint to check Azure AD configuration"""
    from src.tools.auth.azure_auth import azure_scheme

    return {
        "client_id": os.getenv("AZURE_CLIENT_ID"),
        "tenant_id": os.getenv("AZURE_TENANT_ID"),
        "openid_config_loaded": azure_scheme.openid_config.authorization_endpoint is not None,
        "authorization_endpoint": azure_scheme.openid_config.authorization_endpoint,
    }
