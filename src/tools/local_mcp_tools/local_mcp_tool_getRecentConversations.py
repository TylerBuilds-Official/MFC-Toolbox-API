from src.tools.sql_tools.conversations import get_recent_conversations


def oa_get_recent_conversations(days_back: int = 7, limit: int = 10, user_id: int = None):
    """
    Get recent conversations within a time window.
    
    Args:
        days_back: How many days to look back (default 7)
        limit: Maximum results to return (default 10)
        user_id: Injected server-side, not provided by LLM
        
    Returns:
        Dict with recent conversations sorted by last activity
    """
    if user_id is None:
        return {"error": "User context not available"}
    
    try:
        conversations = get_recent_conversations(user_id, days_back, limit)
        return {
            "days_back": days_back,
            "result_count": len(conversations),
            "conversations": conversations
        }
    except Exception as e:
        return {"error": str(e)}


__all__ = ['oa_get_recent_conversations']
