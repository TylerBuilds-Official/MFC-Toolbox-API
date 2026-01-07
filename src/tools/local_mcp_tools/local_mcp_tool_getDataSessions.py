"""
Get Data Sessions Tool

AI-internal tool for retrieving data sessions with flexible filtering and sorting.
Supports date ranges, sorting direction, and various filters.
"""
from src.tools.sql_tools import get_data_sessions_filtered


def oa_get_data_sessions(
    limit: int = 10,
    sort_by: str = 'updated_at',
    sort_order: str = 'desc',
    tool_name: str = None,
    status: str = None,
    after_date: str = None,
    before_date: str = None,
    user_id: int = None
) -> dict:
    """
    Get data sessions with flexible filtering and sorting.
    
    Args:
        limit: Maximum sessions to return (default 10, max 50)
        sort_by: Sort field - 'created_at' or 'updated_at' (default 'updated_at')
        sort_order: Sort direction - 'asc' for oldest first, 'desc' for newest first (default 'desc')
        tool_name: Filter by specific tool (e.g., 'get_machine_production')
        status: Filter by status ('pending', 'running', 'success', 'error')
        after_date: ISO date string - only sessions after this date (e.g., '2025-01-01T00:00:00')
        before_date: ISO date string - only sessions before this date
        user_id: Injected server-side, not provided by LLM
        
    Returns:
        Dict with sessions list and count
        
    Examples:
        - Get 5 most recent sessions: limit=5, sort_order='desc'
        - Get oldest sessions first: sort_order='asc'
        - Get sessions from last week: after_date='2025-01-01T00:00:00'
        - Get only production reports: tool_name='get_machine_production'
    """
    if user_id is None:
        return {"error": "User context not available"}
    
    # Cap limit
    limit = min(max(limit, 1), 50)
    
    try:
        sessions = get_data_sessions_filtered(
            user_id=user_id,
            limit=limit,
            offset=0,
            tool_name=tool_name,
            status=status,
            sort_by=sort_by,
            sort_order=sort_order,
            after_date=after_date,
            before_date=before_date
        )
        
        # Format for AI consumption
        results = []
        for s in sessions:
            results.append({
                "session_id": s['id'],
                "title": s.get('title'),
                "summary": s.get('summary'),
                "tool_name": s['tool_name'],
                "tool_params": s.get('tool_params'),
                "status": s['status'],
                "has_results": s.get('has_results', False),
                "row_count": s.get('row_count'),
                "columns": s.get('columns'),
                "created_at": s['created_at'].isoformat() if s.get('created_at') else None,
                "updated_at": s['updated_at'].isoformat() if s.get('updated_at') else None,
                "parent_session_id": s.get('parent_session_id'),
                "session_group_id": s.get('session_group_id'),
            })
        
        return {
            "sessions": results,
            "count": len(results),
            "filters_applied": {
                "limit": limit,
                "sort_by": sort_by,
                "sort_order": sort_order,
                "tool_name": tool_name,
                "status": status,
                "after_date": after_date,
                "before_date": before_date,
            }
        }
        
    except Exception as e:
        return {"error": str(e)}


__all__ = ['oa_get_data_sessions']
