"""
Updates a conversation project.
"""
import json
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def update_conversation_project(
    project_id: int,
    user_id: int,
    name: str = None,
    description: str = None,
    color: str = None,
    custom_instructions: str = None,
    project_type: str = None,
    permissions: dict = None
) -> bool:
    """
    Updates a conversation project.
    
    Calls Toolbox_UpdateConversationProject stored procedure.
    
    Convention:
        - None = don't change the field
        - '' (empty string) = clear the field
        - any other value = update the field
    
    Args:
        project_id: The project ID
        user_id: User ID for ownership/permission verification
        name: New name (None = no change)
        description: New description (None = no change, '' = clear)
        color: New color (None = no change, '' = clear)
        custom_instructions: New instructions (None = no change, '' = clear)
        project_type: New type (None = no change)
        permissions: New permissions dict (None = no change)
        
    Returns:
        True if update succeeded, False otherwise
        
    Raises:
        Exception: If access denied or project not found
    """
    # Convert permissions dict to JSON string
    permissions_json = None
    if permissions is not None:
        permissions_json = json.dumps(permissions) if permissions else ''
    
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                f"EXEC {SCHEMA}.Toolbox_UpdateConversationProject "
                f"@ProjectId = ?, @UserId = ?, @Name = ?, @Description = ?, "
                f"@Color = ?, @CustomInstructions = ?, @ProjectType = ?, @Permissions = ?",
                (project_id, user_id, name, description, color, 
                 custom_instructions, project_type, permissions_json)
            )
            
            row = cursor.fetchone()
            
            # Consume any additional result sets
            while cursor.nextset():
                pass
            
            cursor.close()
            
            if row and row[0] > 0:
                return True
            return False
            
        except Exception as e:
            cursor.close()
            error_msg = str(e)
            if 'Access denied' in error_msg:
                raise PermissionError("Access denied or project not found")
            raise
