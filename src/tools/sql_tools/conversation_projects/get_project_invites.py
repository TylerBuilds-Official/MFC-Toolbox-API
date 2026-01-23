"""
Gets invites for a project (owner view).
"""
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_project_invites(project_id: int, user_id: int) -> list[dict]:
    """
    Gets all invites for a project (pending, declined, expired).
    
    Only the project owner can view this.
    Calls Toolbox_GetProjectInvites stored procedure.
    
    Args:
        project_id: The project ID
        user_id: User ID for ownership verification
        
    Returns:
        List of invite dicts with status info
        
    Raises:
        PermissionError: If user is not the project owner
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                f"EXEC {SCHEMA}.Toolbox_GetProjectInvites @ProjectId = ?, @UserId = ?",
                (project_id, user_id)
            )
            
            rows = cursor.fetchall()
            
            # Consume any additional result sets
            while cursor.nextset():
                pass
            
            cursor.close()
            
            return [
                {
                    'id':              row[0],
                    'email':           row[1],
                    'status':          row[2],
                    'invited_by_name': row[3],
                    'created_at':      row[4],
                    'expires_at':      row[5],
                    'responded_at':    row[6],
                }
                for row in rows
            ]
            
        except Exception as e:
            cursor.close()
            error_msg = str(e)
            if 'owner' in error_msg.lower() or 'denied' in error_msg.lower():
                raise PermissionError(error_msg)
            raise
