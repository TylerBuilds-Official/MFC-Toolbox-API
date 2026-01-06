"""
Retrieves a list of data sessions for a user.
"""
import json
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_data_sessions_list(
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    tool_name: str = None,
    status: str = None,
    group_id: int = None,
    ungrouped: bool = False
) -> list[dict]:
    """
    Retrieves data sessions for a user with optional filtering.
    Includes result metadata (has_results, row_count) via LEFT JOIN.
    
    Args:
        user_id: The user's ID
        limit: Max number of results (default 50)
        offset: Pagination offset (default 0)
        tool_name: Optional filter by tool name
        status: Optional filter by status
        group_id: Optional filter by group ID
        ungrouped: If True, return only sessions with no group
        
    Returns:
        List of session dictionaries, ordered by UpdatedAt DESC.
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        # LEFT JOIN to DataResults for result metadata
        # Use subquery to get the latest result per session
        query = f"""
            SELECT 
                s.Id, s.UserId, s.MessageId, s.SessionGroupId, s.ParentSessionId,
                s.ToolName, s.ToolParams, s.VisualizationConfig, s.Status, 
                s.ErrorMessage, s.CreatedAt, s.UpdatedAt, s.Title, s.Summary,
                CASE WHEN r.Id IS NOT NULL THEN 1 ELSE 0 END AS HasResults,
                r.[RowCount],
                r.Columns
            FROM {SCHEMA}.DataSessions s
            LEFT JOIN (
                SELECT SessionId, Id, [RowCount], Columns,
                       ROW_NUMBER() OVER (PARTITION BY SessionId ORDER BY CreatedAt DESC) AS rn
                FROM {SCHEMA}.DataResults
            ) r ON s.Id = r.SessionId AND r.rn = 1
            WHERE s.UserId = ? AND s.IsActive = 1
        """
        params = [user_id]
        
        if tool_name:
            query += " AND s.ToolName = ?"
            params.append(tool_name)
        
        if status:
            query += " AND s.Status = ?"
            params.append(status)
        
        if group_id is not None:
            query += " AND s.SessionGroupId = ?"
            params.append(group_id)
        elif ungrouped:
            query += " AND s.SessionGroupId IS NULL"
        
        query += f" ORDER BY s.UpdatedAt DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
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
                'title': row[12],
                'summary': row[13],
                'has_results': bool(row[14]),
                'row_count': row[15],
                'columns': json.loads(row[16]) if row[16] else None,
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
                   ErrorMessage, CreatedAt, UpdatedAt, Title, Summary
            FROM {SCHEMA}.DataSessions
            WHERE SessionGroupId = ? AND IsActive = 1
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
                'title': row[12],
                'summary': row[13],
            })
        
        return sessions
