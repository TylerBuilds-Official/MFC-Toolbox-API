"""
Removes a data session from its group.
"""
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def remove_session_from_group(session_id: int, user_id: int = None) -> bool:
    """
    Removes a data session from its current group.
    Sets SessionGroupId to NULL on the session.
    
    Calls Toolbox_RemoveSessionFromGroup stored procedure.
    
    Args:
        session_id: The session's ID
        user_id: Optional user ID for ownership verification
        
    Returns:
        True if removal succeeded, False otherwise
    """
    # If user_id provided, verify ownership of session
    if user_id is not None:
        with get_mssql_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                f"SELECT UserId FROM {SCHEMA}.DataSessions WHERE Id = ? AND IsActive = 1",
                (session_id,)
            )
            row = cursor.fetchone()
            cursor.close()
            
            if not row or row[0] != user_id:
                return False
    
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"EXEC {SCHEMA}.Toolbox_RemoveSessionFromGroup @SessionId = ?",
            (session_id,)
        )
        
        row = cursor.fetchone()
        
        # Consume any additional result sets
        while cursor.nextset():
            pass
        
        cursor.close()
        
        if row:
            return row[0] > 0  # RowsAffected
        
        return False
