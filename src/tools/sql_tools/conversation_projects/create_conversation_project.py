"""
Creates a new conversation project for a user.
"""
import json
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def create_conversation_project(
    owner_id: int,
    name: str,
    description: str = None,
    color: str = None,
    custom_instructions: str = None,
    project_type: str = 'private',
    permissions: dict = None
) -> int:
    """
    Creates a new conversation project.
    
    Calls Toolbox_CreateConversationProject stored procedure.
    
    Args:
        owner_id: The user's ID
        name: Project name
        description: Optional project description
        color: Optional color (hex or named)
        custom_instructions: Optional custom instructions for AI
        project_type: 'private' | 'shared_locked' | 'shared_open'
        permissions: Optional permissions dict for shared_open projects
        
    Returns:
        The new project's ID
    """
    permissions_json = json.dumps(permissions) if permissions else None
    
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"EXEC {SCHEMA}.Toolbox_CreateConversationProject "
            f"@OwnerId = ?, @Name = ?, @Description = ?, @Color = ?, "
            f"@CustomInstructions = ?, @ProjectType = ?, @Permissions = ?",
            (owner_id, name, description, color, custom_instructions, project_type, permissions_json)
        )
        
        row = cursor.fetchone()
        
        # Consume any additional result sets
        while cursor.nextset():
            pass
        
        cursor.close()
        
        if row:
            return row[0]  # ProjectId
        
        raise Exception("Failed to create conversation project")
