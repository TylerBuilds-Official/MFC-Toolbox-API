"""
Removes a conversation from a project.
"""
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def remove_conversation_from_project(
    conversation_id: int,
    project_id: int,
    user_id: int
) -> bool:
    """
    Removes a conversation from a project.
    
    Calls Toolbox_RemoveConversationFromProject stored procedure.
    
    Args:
        conversation_id: The conversation ID to remove
        project_id: The project ID to remove from
        user_id: User ID for permission verification
        
    Returns:
        True if removal succeeded
        
    Raises:
        PermissionError: If access denied
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                f"EXEC {SCHEMA}.Toolbox_RemoveConversationFromProject "
                f"@ConversationId = ?, @ProjectId = ?, @UserId = ?",
                (conversation_id, project_id, user_id)
            )
            
            row = cursor.fetchone()
            
            # Consume any additional result sets
            while cursor.nextset():
                pass
            
            cursor.close()
            
            return row is not None and row[0] > 0
            
        except Exception as e:
            cursor.close()
            error_msg = str(e)
            if 'Access denied' in error_msg:
                raise PermissionError("Access denied")
            raise
