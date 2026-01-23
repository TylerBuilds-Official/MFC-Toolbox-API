"""
Allows a user to join a shared_open (community) project.
"""
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def join_open_project(project_id: int, user_id: int) -> dict:
    """
    Joins a shared_open project directly (no invite required).
    
    Calls Toolbox_JoinOpenProject stored procedure.
    
    Args:
        project_id: The project to join
        user_id: The user joining
        
    Returns:
        Dict with 'success' and 'message' keys
        
    Raises:
        ValueError: If project is not shared_open or user already a member
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                f"EXEC {SCHEMA}.Toolbox_JoinOpenProject @ProjectId = ?, @UserId = ?",
                (project_id, user_id)
            )
            
            row = cursor.fetchone()
            
            # Consume any additional result sets
            while cursor.nextset():
                pass
            
            cursor.close()
            
            if row:
                return {
                    'success': row[0] == 1,
                    'message': row[1] if len(row) > 1 else 'Joined project'
                }
            
            return {'success': False, 'message': 'Unknown error'}
            
        except Exception as e:
            cursor.close()
            error_msg = str(e)
            if 'not open' in error_msg.lower() or 'already' in error_msg.lower() or 'not found' in error_msg.lower():
                raise ValueError(error_msg)
            raise
