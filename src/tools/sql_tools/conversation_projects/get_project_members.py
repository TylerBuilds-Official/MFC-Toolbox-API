"""
Gets members of a project.
"""
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_project_members(project_id: int, user_id: int) -> list[dict]:
    """
    Gets all members of a project.
    
    Calls Toolbox_GetProjectMembers stored procedure.
    
    Args:
        project_id: The project ID
        user_id: User ID for access verification
        
    Returns:
        List of member dicts with user info and role, owner first
        
    Raises:
        PermissionError: If user doesn't have access to project
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                f"EXEC {SCHEMA}.Toolbox_GetProjectMembers "
                f"@ProjectId = ?, @UserId = ?",
                (project_id, user_id)
            )
            
            rows = cursor.fetchall()
            
            # Consume any additional result sets
            while cursor.nextset():
                pass
            
            cursor.close()
            
            return [
                {
                    'id':           row[0],
                    'user_id':      row[1],
                    'display_name': row[2],
                    'email':        row[3],
                    'role':         row[4],
                    'joined_at':    row[5],
                }
                for row in rows
            ]
            
        except Exception as e:
            cursor.close()
            error_msg = str(e)
            if 'Access denied' in error_msg:
                raise PermissionError("Access denied")
            raise
