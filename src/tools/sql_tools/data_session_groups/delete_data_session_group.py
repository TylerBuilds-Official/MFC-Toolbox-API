"""
Deletes a data session group.
"""
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def delete_data_session_group(group_id: int, user_id: int = None) -> bool:
    """
    Deletes a data session group.
    Sessions in the group are unlinked (SessionGroupId set to NULL), not deleted.
    
    Calls Toolbox_DeleteDataSessionGroup stored procedure.
    
    Args:
        group_id: The group's ID to delete
        user_id: Optional user ID for ownership verification
        
    Returns:
        True if deletion succeeded, False if group not found or not owned
    """
    # If user_id provided, verify ownership first
    if user_id is not None:
        with get_mssql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT UserId FROM {SCHEMA}.DataSessionGroups WHERE Id = ?",
                (group_id,)
            )
            row = cursor.fetchone()
            cursor.close()
            
            if not row or row[0] != user_id:
                return False
    
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"EXEC {SCHEMA}.Toolbox_DeleteDataSessionGroup @GroupId = ?",
            (group_id,)
        )
        
        row = cursor.fetchone()
        
        # Consume any additional result sets
        while cursor.nextset():
            pass
        
        cursor.close()
        
        if row:
            return row[0] > 0  # RowsAffected
        
        return False
