"""
Retrieves a list of data sessions for a user.
"""
import json
from src.tools.sql_tools import get_mssql_connection
from src.tools.sql_tools.mssql_pool import SCHEMA


def get_data_sessions_list(
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    tool_name: str = None,
    status: str = None
) -> list[dict]:
    """
    Retrieves data sessions for a user with optional filtering.
    
    Args:
        user_id: The user's ID
        limit: Max number of results (default 50)
        offset: Pagination offset (default 0)
        tool_name: Optional filter by tool name
        status: Optional filter by status
        
    Returns:
        List of session dictionaries, ordered by UpdatedAt DESC.
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        query = f"""
            SELECT Id, UserId, MessageId, SessionGroupId, ParentSessionId,
                   ToolName, ToolParams, VisualizationConfig, Status, 
                   ErrorMessage, CreatedAt, UpdatedAt
            FROM {SCHEMA}.DataSessions
            WHERE UserId = ?
        """
        params = [user_id]
        
        if tool_name:
            query += " AND ToolName = ?"
            params.append(tool_name)
        
        if status:
            query += " AND Status = ?"
            params.append(status)
        
        query += f" ORDER BY UpdatedAt DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([offset, limit])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        
        sessions = []
        for row in rows:
            sessions.append({
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
            })
        
        return sessions


def get_data_sessions_by_group(group_id: int, user_id: int = None) -> list[dict]:
    """
    Retrieves all sessions in a lineage group.
    
    Args:
        group_id: The SessionGroupId
        user_id: Optional user_id for ownership verification
        
    Returns:
        List of session dictionaries, ordered by CreatedAt ASC (oldest first).
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        query = f"""
            SELECT Id, UserId, MessageId, SessionGroupId, ParentSessionId,
                   ToolName, ToolParams, VisualizationConfig, Status, 
                   ErrorMessage, CreatedAt, UpdatedAt
            FROM {SCHEMA}.DataSessions
            WHERE SessionGroupId = ?
        """
        params = [group_id]
        
        if user_id:
            query += " AND UserId = ?"
            params.append(user_id)
        
        query += " ORDER BY CreatedAt ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        
        sessions = []
        for row in rows:
            sessions.append({
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
            })
        
        return sessions
