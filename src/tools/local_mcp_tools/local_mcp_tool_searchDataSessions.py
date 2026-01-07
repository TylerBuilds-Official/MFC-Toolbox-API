"""
Search Data Sessions Tool

AI-internal tool for searching user's data sessions by keyword.
Searches across title, summary, tool_name, and tool_params.
"""
from src.tools.sql_tools import search_data_sessions


def oa_search_data_sessions(
    query: str,
    limit: int = 15,
    user_id: int = None
) -> dict:
    """
    Search data sessions by keyword.
    
    Args:
        query: Keywords to search for (e.g., 'production', 'job 6516', 'overtime')
        limit: Maximum results to return (default 15, max 50)
        user_id: Injected server-side, not provided by LLM
        
    Returns:
        Dict with query info and ranked session results including match snippets
    """
    if user_id is None:
        return {"error": "User context not available"}
    
    if not query or not query.strip():
        return {"error": "Search query is required"}
    
    try:
        return search_data_sessions(user_id, query.strip(), limit)
    except Exception as e:
        return {"error": str(e)}


__all__ = ['oa_search_data_sessions']
