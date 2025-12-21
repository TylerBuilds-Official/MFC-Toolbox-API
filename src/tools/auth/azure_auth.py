# src/tools/auth/azure_auth.py
"""
Azure AD authentication with manual JWT validation.
Validates JWT tokens from Azure AD and extracts user claims.
"""
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient
import requests

client_id = os.getenv("AZURE_CLIENT_ID")
tenant_id = os.getenv("AZURE_TENANT_ID")

print(f"[AZURE_AUTH] Initializing with Client ID: {client_id}, Tenant ID: {tenant_id}")

security = HTTPBearer()

jwks_uri = f"https://login.microsoftonline.com/{tenant_id}/discovery/keys"
jwks_client = PyJWKClient(jwks_uri)

print(f"[AZURE_AUTH] JWKS URI: {jwks_uri}")
print(f"[AZURE_AUTH] Expected audience: api://{client_id}")


async def azure_scheme(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Validate Azure AD JWT token and return claims.
    Works with both v1.0 and v2.0 tokens.
    """
    token = credentials.credentials
    
    try:
        print(f"[AZURE_AUTH] Validating token...")
        
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=f"api://{client_id}",
            # Allow both v1.0 and v2.0 issuers
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iat": True,
                "verify_aud": True,
                "verify_iss": False,
            }
        )
        
        # Manually verify issuer is from our tenant
        issuer = claims.get("iss", "")
        valid_issuers = [
            f"https://sts.windows.net/{tenant_id}/",  # v1.0
            f"https://login.microsoftonline.com/{tenant_id}/v2.0",  # v2.0
        ]
        
        if issuer not in valid_issuers:
            print(f"[AZURE_AUTH] ❌ Invalid issuer: {issuer}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token issuer"
            )
        
        print(f"[AZURE_AUTH] Token validated successfully")
        print(f"[AZURE_AUTH] User: {claims.get('upn')} ({claims.get('oid')})")
        
        return claims
        
    except jwt.ExpiredSignatureError:
        print(f"[AZURE_AUTH] Token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"})

    except jwt.InvalidAudienceError:
        print(f"[AZURE_AUTH] Invalid audience")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token audience",
            headers={"WWW-Authenticate": "Bearer"})

    except Exception as e:
        print(f"[AZURE_AUTH] Token validation failed: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"})

print(f"[AZURE_AUTH] Manual JWT validation initialized")
