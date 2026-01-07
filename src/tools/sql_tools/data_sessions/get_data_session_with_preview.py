"""
Get full data session details with result preview rows.
Uses stored procedure: Toolbox_GetDataSessionWithPreview
"""
import json
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_data_session_with_preview(
    session_id: int,
    user_id: int = None,
    max_preview_rows: int = 10
) -> dict | None:
    """
    Get full session details including result preview rows.
    
    Args:
        session_id: The session ID
        user_id: Optional user ID for ownership verification
        max_preview_rows: Number of result rows to include (default 10, max 50)
        
    Returns:
        Dict with session details and result preview, or None if not found
    """
    max_preview_rows = min(max(max_preview_rows, 1), 50)
    
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"""EXEC {SCHEMA}.Toolbox_GetDataSessionWithPreview 
                @SessionId=?, @UserId=?, @MaxPreviewRows=?""",
            (session_id, user_id, max_preview_rows)
        )
        
        # Result set 1: Session details
        session_row = cursor.fetchone()
        if not session_row:
            cursor.close()
            return None
        
        session = {
            'id': session_row[0],
            'user_id': session_row[1],
            'message_id': session_row[2],
            'session_group_id': session_row[3],
            'parent_session_id': session_row[4],
            'tool_name': session_row[5],
            'tool_params': json.loads(session_row[6]) if session_row[6] else None,
            'visualization_config': json.loads(session_row[7]) if session_row[7] else None,
            'status': session_row[8],
            'error_message': session_row[9],
            'created_at': session_row[10].isoformat() if session_row[10] else None,
            'updated_at': session_row[11].isoformat() if session_row[11] else None,
            'title': session_row[12],
            'summary': session_row[13],
            'has_results': bool(session_row[14]),
            'result_row_count': session_row[15],
            'result_columns': json.loads(session_row[16]) if session_row[16] else None,
        }
        
        # Result set 2: Preview rows (if exists)
        result_preview = None
        if cursor.nextset():
            preview_row = cursor.fetchone()
            if preview_row:
                result_preview = {
                    'result_id': preview_row[0],
                    'columns': json.loads(preview_row[1]) if preview_row[1] else None,
                    'row_count': preview_row[2],
                    'result_created_at': preview_row[3].isoformat() if preview_row[3] else None,
                    'preview_rows': json.loads(preview_row[4]) if preview_row[4] else None,
                }
        
        cursor.close()
        
        return {
            'session': session,
            'result_preview': result_preview,
        }
