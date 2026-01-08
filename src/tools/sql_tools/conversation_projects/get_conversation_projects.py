"""
Gets which projects a conversation belongs to.
"""
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_conversation_projects(conversation_id: int, user_id: int) -> list[dict]:
    """
    Gets all projects a conversation belongs to.
    
    Calls Toolbox_GetConversationProjects stored procedure.
    
    Args:
        conversation_id: The conversation ID
        user_id: User ID for ownership verification
        
    Returns:
        List of project summary dicts with id, name, color, project_type
        
    Raises:
        PermissionError: If conversation not owned by user
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                f"EXEC {SCHEMA}.Toolbox_GetConversationProjects "
                f"@ConversationId = ?, @UserId = ?",
                (conversation_id, user_id)
            )
            
            rows = cursor.fetchall()
            
            # Consume any additional result sets
            while cursor.nextset():
                pass
            
            cursor.close()
            
            return [
                {
                    'id':           row[0],
                    'name':         row[1],
                    'color':        row[2],
                    'project_type': row[3],
                }
                for row in rows
            ]
            
        except Exception as e:
            cursor.close()
            error_msg = str(e)
            if 'access denied' in error_msg.lower() or 'not found' in error_msg.lower():
                raise PermissionError("Conversation not found or access denied")
            raise
