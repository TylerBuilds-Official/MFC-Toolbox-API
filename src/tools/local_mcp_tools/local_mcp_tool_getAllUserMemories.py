from src.utils.memory_utils import MemoryService


def oa_get_all_user_memories(
    memory_type: str = None,
    user_id: int = None
):
    """
    Get all memories about this user. Use when you need a complete picture
    of what you know, or when asked 'what do you know about me?'
    
    Args:
        memory_type: Filter by type (optional) - 'fact', 'preference', 'project', 'skill', 'context'
        user_id: Injected server-side, not provided by LLM
        
    Returns:
        All memories, optionally filtered by type
    """
    if user_id is None:
        return {"error": "User context not available"}
    
    # Validate memory_type if provided
    if memory_type is not None:
        valid_types = {"fact", "preference", "project", "skill", "context"}
        if memory_type not in valid_types:
            return {"error": f"Invalid memory_type '{memory_type}'. Must be one of: {valid_types}"}
    
    try:
        memories = MemoryService.get_all_memories(user_id, memory_type=memory_type)
        stats = MemoryService.get_memory_stats(user_id)
        
        return {
            "total": len(memories),
            "stats": stats,
            "memories": [
                {
                    "id": m.id,
                    "type": m.memory_type,
                    "content": m.content,
                    "created_at": m.created_at.isoformat() if hasattr(m.created_at, 'isoformat') else str(m.created_at),
                    "reference_count": m.reference_count,
                    "last_referenced_at": m.last_referenced_at.isoformat() if m.last_referenced_at and hasattr(m.last_referenced_at, 'isoformat') else None,
                    "is_stale": m.is_stale,
                    "expires_at": m.expires_at.isoformat() if m.expires_at and hasattr(m.expires_at, 'isoformat') else None
                }
                for m in memories
            ]
        }
    except Exception as e:
        return {"error": str(e)}


__all__ = ['oa_get_all_user_memories']
