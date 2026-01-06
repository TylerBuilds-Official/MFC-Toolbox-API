"""
Retrieves a data session by ID.
"""
import json
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_data_session(session_id: int, user_id: int = None) -> dict | None:
    """
    Retrieves a data session by ID.
    Optionally filters by user_id for ownership verification.
    
    Returns:
        Dictionary with session fields, or None if not found.
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute(
                f"""
                SELECT Id, UserId, MessageId, SessionGroupId, ParentSessionId,
                       ToolName, ToolParams, VisualizationConfig, Status, 
                       ErrorMessage, CreatedAt, UpdatedAt, Title, Summary
                FROM {SCHEMA}.DataSessions
                WHERE Id = ? AND UserId = ? AND IsActive = 1
                """,
                (session_id, user_id)
            )
        else:
            cursor.execute(
                f"""
                SELECT Id, UserId, MessageId, SessionGroupId, ParentSessionId,
                       ToolName, ToolParams, VisualizationConfig, Status, 
                       ErrorMessage, CreatedAt, UpdatedAt, Title, Summary
                FROM {SCHEMA}.DataSessions
                WHERE Id = ? AND IsActive = 1
                """,
                (session_id,)
            )
        
        row = cursor.fetchone()
        cursor.close()
        
        if row is None:
            return None
        
        return {
            'id': row[0],
            'user_id': row[1],
            'message_id': row[2],
            'session_group_id': row[3],
            'parent_session_id': row[4],
            'tool_name': row[5],
            'tool_params': json.loads(row[6]) if row[6] else None,
            'visualization_config': json.loads(row[7]) if row[7] else None,
            'status': row[8],
            'error_message': row[9],
            'created_at': row[10],
            'updated_at': row[11],
            'title': row[12],
            'summary': row[13],
        }
