"""
Session lineage functions - root finding and lineage traversal.
Uses stored procedures: Toolbox_GetRootSessionId, Toolbox_GetSessionLineageByRoot
"""
import json
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_root_session_id(session_id: int, user_id: int = None) -> dict | None:
    """
    Walk up the parent chain to find the root session.
    
    Args:
        session_id: The session ID to start from
        user_id: Optional user ID for ownership verification
        
    Returns:
        Dict with root_session_id and chain_depth, or None if session not found
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"EXEC {SCHEMA}.Toolbox_GetRootSessionId @SessionId=?, @UserId=?",
            (session_id, user_id)
        )
        
        row = cursor.fetchone()
        cursor.close()
        
        if not row:
            return None
        
        return {
            'root_session_id': row[0],
            'chain_depth': row[1],
        }


def get_session_lineage_by_root(root_session_id: int, user_id: int = None) -> list[dict]:
    """
    Get all sessions in a lineage chain starting from the root.
    Uses recursive CTE to find all descendants.
    
    Args:
        root_session_id: The root session ID
        user_id: Optional user ID for ownership verification
        
    Returns:
        List of session dicts ordered by depth then created_at
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"EXEC {SCHEMA}.Toolbox_GetSessionLineageByRoot @RootSessionId=?, @UserId=?",
            (root_session_id, user_id)
        )
        
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
                'depth': row[14],
                'has_results': bool(row[15]),
                'row_count': row[16],
                'columns': json.loads(row[17]) if row[17] else None,
            })
        
        return sessions


def get_full_session_lineage(session_id: int, user_id: int = None) -> dict | None:
    """
    Convenience function: finds root from any session, then returns full lineage.
    
    Args:
        session_id: Any session ID in the lineage chain
        user_id: Optional user ID for ownership verification
        
    Returns:
        Dict with root_session_id and all sessions in lineage, or None if not found
    """
    root_info = get_root_session_id(session_id, user_id)
    if not root_info:
        return None
    
    sessions = get_session_lineage_by_root(root_info['root_session_id'], user_id)
    
    return {
        'root_session_id': root_info['root_session_id'],
        'chain_depth': root_info['chain_depth'],
        'sessions': sessions,
        'session_count': len(sessions),
    }
