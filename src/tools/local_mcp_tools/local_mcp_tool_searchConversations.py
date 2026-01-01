from src.tools.sql_tools import search_conversations


def oa_search_conversations(query: str, limit: int = 10, user_id: int = None):
    """
    Search past conversations by keyword.
    
    Args:
        query: Keywords to search for
        limit: Maximum results to return (default 10)
        user_id: Injected server-side, not provided by LLM
        
    Returns:
        Dict with query info and ranked conversation results
    """
    if user_id is None:
        return {"error": "User context not available"}
    
    if not query or not query.strip():
        return {"error": "Search query is required"}
    
    try:
        return search_conversations(user_id, query, limit)
    except Exception as e:
        return {"error": str(e)}


__all__ = ['oa_search_conversations']
