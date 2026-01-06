"""
Creates a new data session group for a user.
"""
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def create_data_session_group(
    user_id: int,
    name: str,
    description: str = None,
    color: str = None
) -> int:
    """
    Creates a new data session group.
    
    Calls Toolbox_CreateDataSessionGroup stored procedure.
    
    Args:
        user_id: The user's ID
        name: Group name
        description: Optional group description
        color: Optional color (hex or named)
        
    Returns:
        The new group's ID
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"EXEC {SCHEMA}.Toolbox_CreateDataSessionGroup "
            f"@UserId = ?, @Name = ?, @Description = ?, @Color = ?",
            (user_id, name, description, color)
        )
        
        row = cursor.fetchone()
        
        # Consume any additional result sets
        while cursor.nextset():
            pass
        
        cursor.close()
        
        if row:
            return row[0]  # GroupId
        
        raise Exception("Failed to create data session group")
