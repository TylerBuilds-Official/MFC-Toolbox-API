"""
API endpoints for user memory management.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Literal

from src.tools.auth import User, require_active_user
from src.utils.memory_utils import MemoryService


router = APIRouter()


# ============================================================================
# Request Models
# ============================================================================

class CreateMemoryRequest(BaseModel):
    """Request body for creating a memory."""
    content: str
    memory_type: Literal['fact', 'preference', 'project', 'skill', 'context'] = 'fact'
    expires_at: Optional[str] = None  # ISO datetime string


class UpdateMemoryRequest(BaseModel):
    """Request body for updating a memory."""
    content: Optional[str] = None
    memory_type: Optional[Literal['fact', 'preference', 'project', 'skill', 'context']] = None
    expires_at: Optional[str] = None  # ISO datetime string, or empty string to clear


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/memories")
async def list_memories(
    memory_type: str = None,
    include_inactive: bool = False,
    user: User = Depends(require_active_user)
):
    """
    List all memories for the current user.
    
    Args:
        memory_type: Filter by type (optional)
        include_inactive: Include soft-deleted memories (default False)
    """
    memories = MemoryService.get_all_memories(
        user.id, 
        memory_type=memory_type,
        include_inactive=include_inactive
    )
    
    return {
        "memories": [m.to_dict() for m in memories],
        "count": len(memories)
    }


@router.get("/memories/stale")
async def get_stale_memories(
    days: int = 90,
    user: User = Depends(require_active_user)
):
    """
    Get memories that haven't been referenced in X days.
    Used for stale memory review.
    
    Args:
        days: Days without reference to consider stale (default 90)
    """
    memories = MemoryService.get_stale_memories(user.id, days)
    
    return {
        "memories": [m.to_dict() for m in memories],
        "count": len(memories),
        "stale_threshold_days": days
    }


@router.get("/memories/stats")
async def get_memory_stats(user: User = Depends(require_active_user)):
    """
    Get statistics about user's memories.
    """
    stats = MemoryService.get_memory_stats(user.id)
    return stats


@router.get("/memories/{memory_id}")
async def get_memory(
    memory_id: int,
    user: User = Depends(require_active_user)
):
    """
    Get a single memory by ID.
    """
    memory = MemoryService.get_memory(memory_id, user.id)
    
    if memory is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return memory.to_dict()


@router.post("/memories")
async def create_memory(
    body: CreateMemoryRequest,
    user: User = Depends(require_active_user)
):
    """
    Create a new memory.
    """
    try:
        memory = MemoryService.create_memory(
            user_id=user.id,
            content=body.content,
            memory_type=body.memory_type,
            expires_at=body.expires_at
        )
        return memory.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/memories/{memory_id}")
async def update_memory(
    memory_id: int,
    body: UpdateMemoryRequest,
    user: User = Depends(require_active_user)
):
    """
    Update a memory's content, type, or expiration.
    """
    updates = {}
    if body.content is not None:
        updates["content"] = body.content
    if body.memory_type is not None:
        updates["memory_type"] = body.memory_type
    if body.expires_at is not None:
        # Empty string means clear expiration
        updates["expires_at"] = body.expires_at if body.expires_at else None
    
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    try:
        memory = MemoryService.update_memory(memory_id, user.id, updates)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if memory is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return memory.to_dict()


@router.post("/memories/{memory_id}/refresh")
async def refresh_memory(
    memory_id: int,
    user: User = Depends(require_active_user)
):
    """
    Refresh a memory's staleness.
    Confirms the memory is still relevant without changing content.
    """
    success = MemoryService.refresh_memory(memory_id, user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return {"success": True, "message": "Memory refreshed"}


@router.delete("/memories/{memory_id}")
async def delete_memory(
    memory_id: int,
    user: User = Depends(require_active_user)
):
    """
    Soft delete a memory.
    """
    success = MemoryService.delete_memory(memory_id, user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return {"success": True, "message": "Memory deleted"}


@router.post("/memories/search")
async def search_memories(
    query: str,
    limit: int = 10,
    user: User = Depends(require_active_user)
):
    """
    Search memories by keyword.
    Updates reference tracking for results.
    """
    memories = MemoryService.search(user.id, query, limit, track_reference=True)
    
    return {
        "memories": [m.to_dict() for m in memories],
        "count": len(memories),
        "query": query
    }
