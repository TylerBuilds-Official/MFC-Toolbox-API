"""
Adds a conversation to a project.
"""
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def add_conversation_to_project(
    conversation_id: int,
    project_id: int,
    user_id: int
) -> dict:
    """
    Adds a conversation to a project.
    
    Calls Toolbox_AddConversationToProject stored procedure.
    
    Args:
        conversation_id: The conversation ID to add
        project_id: The project ID to add to
        user_id: User ID for permission verification
        
    Returns:
        Dict with 'success' and 'message' keys
        
    Raises:
        PermissionError: If access denied
        ValueError: If conversation or project not found
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                f"EXEC {SCHEMA}.Toolbox_AddConversationToProject "
                f"@ConversationId = ?, @ProjectId = ?, @UserId = ?",
                (conversation_id, project_id, user_id)
            )
            
            row = cursor.fetchone()
            
            # Consume any additional result sets
            while cursor.nextset():
                pass
            
            cursor.close()
            
            if row:
                return {
                    'success': bool(row[0]),
                    'message': row[1] if len(row) > 1 else 'Added to project'
                }
            
            return {'success': False, 'message': 'Unknown error'}
            
        except Exception as e:
            cursor.close()
            error_msg = str(e)
            if 'access denied' in error_msg.lower():
                raise PermissionError(error_msg)
            if 'not found' in error_msg.lower():
                raise ValueError(error_msg)
            raise
