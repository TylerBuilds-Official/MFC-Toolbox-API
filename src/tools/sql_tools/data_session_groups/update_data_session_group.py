"""
Updates a data session group.
"""
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def update_data_session_group(
    group_id: int,
    user_id: int = None,
    name: str = None,
    description: str = None,
    color: str = None
) -> bool:
    """
    Updates a data session group.
    
    Calls Toolbox_UpdateDataSessionGroup stored procedure.
    
    Convention:
        - None = don't change the field
        - '' (empty string) = clear the field (set to NULL)
        - any other value = update the field
    
    Args:
        group_id: The group's ID to update
        user_id: Optional user ID for ownership verification
        name: New name (None = no change)
        description: New description (None = no change, '' = clear)
        color: New color (None = no change, '' = clear)
        
    Returns:
        True if update succeeded, False if group not found or not owned
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
            f"EXEC {SCHEMA}.Toolbox_UpdateDataSessionGroup "
            f"@GroupId = ?, @Name = ?, @Description = ?, @Color = ?",
            (group_id, name, description, color)
        )
        
        row = cursor.fetchone()
        
        # Consume any additional result sets
        while cursor.nextset():
            pass
        
        cursor.close()
        
        if row:
            return row[0] > 0  # RowsAffected
        
        return False
