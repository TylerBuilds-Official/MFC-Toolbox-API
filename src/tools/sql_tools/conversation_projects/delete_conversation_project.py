"""
Deletes a conversation project (soft delete).
"""
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def delete_conversation_project(
    project_id: int,
    user_id: int,
    delete_conversations: bool = False
) -> bool:
    """
    Soft deletes a conversation project.
    
    Calls Toolbox_DeleteConversationProject stored procedure.
    
    Args:
        project_id: The project ID
        user_id: User ID for ownership verification (only owner can delete)
        delete_conversations: If True, deletes conversations that are ONLY 
                              in this project (not in any other projects)
        
    Returns:
        True if delete succeeded
        
    Raises:
        Exception: If access denied or project not found
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                f"EXEC {SCHEMA}.Toolbox_DeleteConversationProject "
                f"@ProjectId = ?, @UserId = ?, @DeleteConversations = ?",
                (project_id, user_id, 1 if delete_conversations else 0)
            )
            
            row = cursor.fetchone()
            
            # Consume any additional result sets
            while cursor.nextset():
                pass
            
            cursor.close()
            
            return row is not None and row[0] == 1
            
        except Exception as e:
            cursor.close()
            error_msg = str(e)
            if 'Access denied' in error_msg:
                raise PermissionError("Access denied or project not found")
            raise
