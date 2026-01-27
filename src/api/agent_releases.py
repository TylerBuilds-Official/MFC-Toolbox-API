"""
Agent Release Management API

Endpoints for uploading agent releases, checking versions, and downloading updates.
Network share location: \\\\10.0.15.1\\IT_Services\\Services\\Tyler\\Fabcore\\LocalAgent
"""

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import FileResponse

from src.utils.agent_utils import agent_registry
from src.tools.auth import User, get_current_user

router = APIRouter(prefix="/agent")

import os

# =============================================================================
# Configuration
# =============================================================================

# Agent release storage paths
# For local testing: set AGENT_RELEASES_LOCAL=true in .env
# Production uses network share, local dev uses local filesystem
_USE_LOCAL_STORAGE = os.getenv("AGENT_RELEASES_LOCAL", "").lower() in ("true", "1", "yes")

if _USE_LOCAL_STORAGE:
    # Local development - use a folder next to the API
    _LOCAL_ROOT = Path(__file__).parent.parent.parent.parent / "agent_releases_local"
    AGENT_RELEASES_DIR = _LOCAL_ROOT / "releases"
    AGENT_ARCHIVE_DIR = _LOCAL_ROOT / "archive"
    print(f"[AGENT_RELEASES] Using LOCAL storage: {_LOCAL_ROOT}")
else:
    # Production - use network share
    FABCORE_ROOT = Path(r"\\10.0.15.1\IT_Services\Services\Tyler\Fabcore")
    AGENT_ROOT = FABCORE_ROOT / "LocalAgent"
    AGENT_RELEASES_DIR = AGENT_ROOT / "releases"
    AGENT_ARCHIVE_DIR = AGENT_ROOT / "archive"
    print(f"[AGENT_RELEASES] Using NETWORK storage: {AGENT_RELEASES_DIR}")


def ensure_directories():
    """Ensure release directories exist."""
    try:
        AGENT_RELEASES_DIR.mkdir(parents=True, exist_ok=True)
        AGENT_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        (AGENT_RELEASES_DIR / "latest").mkdir(exist_ok=True)
    except Exception as e:
        print(f"[AGENT_RELEASES] Warning: Could not create directories: {e}")


# =============================================================================
# Version Endpoints (Used by agents)
# =============================================================================

@router.get("/version")
async def get_latest_version():
    """
    Get latest agent version info.
    
    Called by: Agents on startup to check for updates
    
    Returns:
        Version info dict with version, force flag, changelog, etc.
    """
    version_file = AGENT_RELEASES_DIR / "latest" / "version.json"
    
    if not version_file.exists():
        raise HTTPException(
            status_code=404,
            detail="No agent releases found. Upload a release first."
        )
    
    try:
        with open(version_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read version info: {e}"
        )


@router.get("/download/{version}")
async def download_release(version: str):
    """
    Download a specific agent release.
    
    Called by: Agents when applying updates
    
    Args:
        version: Version to download (e.g., "1.2.0")
        
    Returns:
        Zip file containing the agent release
    """
    zip_path = AGENT_RELEASES_DIR / version / f"FabCoreAgent_{version}.zip"
    
    if not zip_path.exists():
        # Also check latest
        latest_zip = AGENT_RELEASES_DIR / "latest" / f"FabCoreAgent_{version}.zip"
        if latest_zip.exists():
            zip_path = latest_zip
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Version {version} not found"
            )
    
    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename=f"FabCoreAgent_{version}.zip"
    )


# =============================================================================
# Release Management Endpoints (Used by admin/you)
# =============================================================================

@router.post("/release")
async def upload_release(
    version: str = Form(..., description="Version number (e.g., 1.2.0, 1.2.0a)"),
    changelog: str = Form("", description="What's new in this version"),
    force: bool = Form(False, description="Force all agents to update immediately"),
    min_version: Optional[str] = Form(None, description="Minimum version required"),
    file: UploadFile = File(..., description="FabCoreAgent zip file"),
    # user: User = Depends(get_current_user)  # TODO: Re-enable auth after testing
):
    """
    Upload a new agent release and notify all connected agents.
    
    Called by: You (admin) via curl, Postman, or admin UI
    
    This endpoint:
    1. Saves the zip to the releases directory
    2. Creates version.json metadata
    3. Updates the 'latest' pointer
    4. Archives the release (permanent copy)
    5. Broadcasts update notification to all connected agents
    
    Example curl:
        curl -X POST "http://localhost:8000/agent/release" \\
            -F "version=1.2.0" \\
            -F "changelog=Bug fixes and improvements" \\
            -F "force=false" \\
            -F "file=@FabCoreAgent_1.2.0.zip"
    """
    # Validate version format - allow semantic versioning with optional suffix
    # Valid: 1.2.0, 1.2.0a, 1.2.0b, 1.2.0-alpha, 1.2.0-beta.1
    version_pattern = r'^\d+\.\d+\.\d+[a-zA-Z0-9\-\.]*$'
    if not re.match(version_pattern, version):
        raise HTTPException(
            status_code=400,
            detail="Invalid version format. Use semantic versioning (e.g., 1.2.0, 1.2.0a, 1.2.0-beta)"
        )
    
    # Ensure directories exist
    ensure_directories()
    
    # Create version-specific directory
    release_dir = AGENT_RELEASES_DIR / version
    try:
        release_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create release directory: {e}"
        )
    
    # Save the zip file
    zip_path = release_dir / f"FabCoreAgent_{version}.zip"
    try:
        with open(zip_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        print(f"[AGENT_RELEASES] Saved zip: {zip_path}")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save zip file: {e}"
        )
    
    # Create version.json metadata
    version_info = {
        "version": version,
        "force": force,
        "changelog": changelog,
        "min_version": min_version,
        "download_url": f"/agent/download/{version}",
        "release_date": datetime.now().isoformat(),
        "released_by": "admin"  # TODO: user.name when auth re-enabled
    }
    
    version_json_path = release_dir / "version.json"
    try:
        with open(version_json_path, 'w') as f:
            json.dump(version_info, f, indent=2)
        print(f"[AGENT_RELEASES] Created version.json: {version_json_path}")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create version.json: {e}"
        )
    
    # Update 'latest' directory
    latest_dir = AGENT_RELEASES_DIR / "latest"
    try:
        # Clear existing latest
        if latest_dir.exists():
            shutil.rmtree(latest_dir)
        # Copy new release to latest
        shutil.copytree(release_dir, latest_dir)
        print(f"[AGENT_RELEASES] Updated latest to {version}")
    except Exception as e:
        print(f"[AGENT_RELEASES] Warning: Failed to update latest: {e}")
    
    # Archive the release (permanent copy)
    archive_dir = AGENT_ARCHIVE_DIR / version
    try:
        if not archive_dir.exists():
            shutil.copytree(release_dir, archive_dir)
            print(f"[AGENT_RELEASES] Archived to: {archive_dir}")
    except Exception as e:
        print(f"[AGENT_RELEASES] Warning: Failed to archive: {e}")
    
    # Broadcast update notification to all connected agents
    agents_notified = await agent_registry.broadcast_update_notification(
        version=version,
        force=force,
        changelog=changelog,
        download_url=f"/agent/download/{version}",
        min_version=min_version
    )
    
    return {
        "success": True,
        "version": version,
        "force": force,
        "changelog": changelog,
        "agents_notified": agents_notified,
        "release_path": str(release_dir),
        "archive_path": str(archive_dir)
    }


@router.post("/notify")
async def notify_update(
    version: str = Form(None, description="Version to notify about (defaults to latest)"),
    force: bool = Form(False, description="Force update flag"),
    # user: User = Depends(get_current_user)  # TODO: Re-enable auth after testing
):
    """
    Re-broadcast update notification without uploading a new release.
    
    Useful if some agents missed the initial notification or you want
    to change the force flag for an existing release.
    """
    # Get version info
    if version:
        version_file = AGENT_RELEASES_DIR / version / "version.json"
    else:
        version_file = AGENT_RELEASES_DIR / "latest" / "version.json"
    
    if not version_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Version {'latest' if not version else version} not found"
        )
    
    with open(version_file, 'r') as f:
        version_info = json.load(f)
    
    # Override force flag if specified
    if force:
        version_info["force"] = True
    
    # Broadcast
    agents_notified = await agent_registry.broadcast_update_notification(
        version=version_info["version"],
        force=version_info.get("force", False),
        changelog=version_info.get("changelog", ""),
        download_url=version_info.get("download_url"),
        min_version=version_info.get("min_version")
    )
    
    return {
        "success": True,
        "version": version_info["version"],
        "force": version_info.get("force", False),
        "agents_notified": agents_notified
    }


@router.get("/releases")
async def list_releases():
    """
    List all available agent releases.
    """
    releases = []
    
    try:
        if not AGENT_RELEASES_DIR.exists():
            return {"releases": [], "count": 0, "latest": None}
            
        for item in AGENT_RELEASES_DIR.iterdir():
            if item.is_dir() and item.name != "latest":
                version_file = item / "version.json"
                if version_file.exists():
                    with open(version_file, 'r') as f:
                        info = json.load(f)
                        releases.append(info)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list releases: {e}"
        )
    
    # Sort by release date (newest first)
    releases.sort(key=lambda x: x.get("release_date", ""), reverse=True)
    
    return {
        "releases": releases,
        "count": len(releases),
        "latest": releases[0]["version"] if releases else None
    }


@router.delete("/release/{version}")
async def delete_release(
    version: str,
    # user: User = Depends(get_current_user)  # TODO: Re-enable auth after testing
):
    """
    Delete a release from the releases directory.
    
    Note: Does NOT delete from archive (archives are permanent).
    """
    release_dir = AGENT_RELEASES_DIR / version
    
    if not release_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Version {version} not found"
        )
    
    # Check if this is the latest
    latest_version_file = AGENT_RELEASES_DIR / "latest" / "version.json"
    is_latest = False
    if latest_version_file.exists():
        with open(latest_version_file, 'r') as f:
            latest_info = json.load(f)
            is_latest = latest_info.get("version") == version
    
    if is_latest:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete the latest release. Upload a new version first."
        )
    
    try:
        shutil.rmtree(release_dir)
        return {
            "success": True,
            "message": f"Deleted release {version}",
            "archived": (AGENT_ARCHIVE_DIR / version).exists()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete release: {e}"
        )
