from src.utils.memory_utils import MemoryService


def oa_search_user_memories(query: str, limit: int = 10, user_id: int = None):
    """
    Search user's memories by keyword.
    
    Args:
        query: Search keywords
        limit: Maximum results to return
        user_id: Injected server-side, not provided by LLM
        
    Returns:
        List of matching memories
    """
    if user_id is None:
        return {"error": "User context not available"}
    
    try:
        memories = MemoryService.search(user_id, query, limit)
        return {
            "found": len(memories),
            "memories": [
                {
                    "id": m.id,
                    "type": m.memory_type,
                    "content": m.content,
                    "source_conversation_id": m.source_conversation_id,
                    "created_at": m.created_at.isoformat() if hasattr(m.created_at, 'isoformat') else str(m.created_at)
                }
                for m in memories
            ]
        }
    except Exception as e:
        return {"error": str(e)}


__all__ = ['oa_search_user_memories']
