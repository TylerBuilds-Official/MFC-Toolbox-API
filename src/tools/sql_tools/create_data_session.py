"""
Creates a new data session in the database.
"""
import json
from src.tools.sql_tools import get_mssql_connection
from src.tools.sql_tools.mssql_pool import SCHEMA


def create_data_session(
    user_id: int,
    tool_name: str,
    tool_params: dict = None,
    message_id: int = None,
    parent_session_id: int = None,
    visualization_config: dict = None
) -> dict:
    """
    Creates a new data session with status='pending'.
    SessionGroupId is auto-assigned by trigger.
    
    Returns:
        Dictionary with all session fields including the new Id.
    """
    tool_params_json = json.dumps(tool_params) if tool_params else None
    viz_config_json = json.dumps(visualization_config) if visualization_config else None
    
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO {SCHEMA}.DataSessions 
                (UserId, MessageId, ParentSessionId, ToolName, ToolParams, 
                 VisualizationConfig, Status, ErrorMessage)
            OUTPUT 
                INSERTED.Id, INSERTED.UserId, INSERTED.MessageId, 
                INSERTED.SessionGroupId, INSERTED.ParentSessionId,
                INSERTED.ToolName, INSERTED.ToolParams, INSERTED.VisualizationConfig,
                INSERTED.Status, INSERTED.ErrorMessage, 
                INSERTED.CreatedAt, INSERTED.UpdatedAt
            VALUES (?, ?, ?, ?, ?, ?, 'pending', NULL)
            """,
            (user_id, message_id, parent_session_id, tool_name, 
             tool_params_json, viz_config_json)
        )
        row = cursor.fetchone()
        cursor.close()
        
        # Note: SessionGroupId will be NULL immediately after INSERT
        # The trigger fires AFTER INSERT, so we need to re-fetch to get it
        session_id = row[0]
        
    # Re-fetch to get the trigger-assigned SessionGroupId
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT SessionGroupId FROM {SCHEMA}.DataSessions WHERE Id = ?",
            (session_id,)
        )
        group_row = cursor.fetchone()
        cursor.close()
        session_group_id = group_row[0] if group_row else None

    return {
        'id': row[0],
        'user_id': row[1],
        'message_id': row[2],
        'session_group_id': session_group_id,
        'parent_session_id': row[4],
        'tool_name': row[5],
        'tool_params': json.loads(row[6]) if row[6] else None,
        'visualization_config': json.loads(row[7]) if row[7] else None,
        'status': row[8],
        'error_message': row[9],
        'created_at': row[10],
        'updated_at': row[11],
    }
