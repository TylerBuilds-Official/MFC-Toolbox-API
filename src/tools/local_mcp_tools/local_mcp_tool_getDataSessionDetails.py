"""
Get Data Session Details Tool

AI-internal tool for retrieving full session details including result preview.
Use after search or get_data_sessions to dive deeper into a specific session.
"""
from src.tools.sql_tools import get_data_session_with_preview


def oa_get_data_session_details(
    session_id: int,
    max_preview_rows: int = 10,
    user_id: int = None
) -> dict:
    """
    Get full details for a specific data session including result preview.
    
    Args:
        session_id: The session ID to retrieve (required)
        max_preview_rows: Number of result rows to include in preview (default 10, max 50)
        user_id: Injected server-side, not provided by LLM
        
    Returns:
        Dict with full session details and result preview rows for summarization
        
    Use this after search_data_sessions or get_data_sessions when you need:
        - Full tool parameters that were used
        - Actual data preview to describe or summarize
        - Parent session info for lineage context
    """
    if user_id is None:
        return {"error": "User context not available"}
    
    if not session_id:
        return {"error": "session_id is required"}
    
    try:
        result = get_data_session_with_preview(
            session_id=session_id,
            user_id=user_id,
            max_preview_rows=max_preview_rows
        )
        
        if not result:
            return {"error": f"Session {session_id} not found or access denied"}
        
        session = result['session']
        preview = result.get('result_preview')
        
        # Build response
        response = {
            "session": {
                "session_id": session['id'],
                "title": session.get('title'),
                "summary": session.get('summary'),
                "tool_name": session['tool_name'],
                "tool_params": session.get('tool_params'),
                "status": session['status'],
                "error_message": session.get('error_message'),
                "created_at": session.get('created_at'),
                "updated_at": session.get('updated_at'),
                "parent_session_id": session.get('parent_session_id'),
                "session_group_id": session.get('session_group_id'),
                "has_results": session.get('has_results', False),
                "result_row_count": session.get('result_row_count'),
                "result_columns": session.get('result_columns'),
            }
        }
        
        # Include result preview if available
        if preview:
            response["result_preview"] = {
                "columns": preview.get('columns'),
                "row_count": preview.get('row_count'),
                "preview_row_count": len(preview.get('preview_rows') or []),
                "preview_rows": preview.get('preview_rows'),
            }
            
            # Add helpful context for AI
            if preview.get('row_count') and preview.get('preview_rows'):
                shown = len(preview['preview_rows'])
                total = preview['row_count']
                if shown < total:
                    response["note"] = f"Showing {shown} of {total} total rows. Full data available on the Data page."
        
        return response
        
    except Exception as e:
        return {"error": str(e)}


__all__ = ['oa_get_data_session_details']
