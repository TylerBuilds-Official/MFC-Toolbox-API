"""
Adds a data session to a group.
"""
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def add_session_to_group(session_id: int, group_id: int, user_id: int = None) -> bool:
    """
    Adds a data session to a group.
    
    Calls Toolbox_AddSessionToGroup stored procedure.
    
    Args:
        session_id: The session's ID
        group_id: The group's ID to add the session to
        user_id: Optional user ID for ownership verification
        
    Returns:
        True if assignment succeeded, False otherwise
    """
    # If user_id provided, verify ownership of both session and group
    if user_id is not None:
        with get_mssql_connection() as conn:
            cursor = conn.cursor()
            
            # Check session ownership
            cursor.execute(
                f"SELECT UserId FROM {SCHEMA}.DataSessions WHERE Id = ? AND IsActive = 1",
                (session_id,)
            )
            session_row = cursor.fetchone()
            
            if not session_row or session_row[0] != user_id:
                cursor.close()
                return False
            
            # Check group ownership
            cursor.execute(
                f"SELECT UserId FROM {SCHEMA}.DataSessionGroups WHERE Id = ?",
                (group_id,)
            )
            group_row = cursor.fetchone()
            cursor.close()
            
            if not group_row or group_row[0] != user_id:
                return False
    
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"EXEC {SCHEMA}.Toolbox_AddSessionToGroup @SessionId = ?, @GroupId = ?",
            (session_id, group_id)
        )
        
        row = cursor.fetchone()
        
        # Consume any additional result sets
        while cursor.nextset():
            pass
        
        cursor.close()
        
        if row:
            return row[0] > 0  # RowsAffected
        
        return False
