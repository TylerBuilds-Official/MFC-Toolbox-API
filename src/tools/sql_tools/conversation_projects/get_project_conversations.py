"""
Gets all conversations in a project.
"""
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_project_conversations(project_id: int, user_id: int) -> list[dict]:
    """
    Gets all conversations in a project.
    
    Calls Toolbox_GetProjectConversations stored procedure.
    
    Args:
        project_id: The project ID
        user_id: User ID for access verification
        
    Returns:
        List of conversation dicts with project membership info
        
    Raises:
        PermissionError: If user doesn't have access to project
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                f"EXEC {SCHEMA}.Toolbox_GetProjectConversations "
                f"@ProjectId = ?, @UserId = ?",
                (project_id, user_id)
            )
            
            rows = cursor.fetchall()
            
            # Consume any additional result sets
            while cursor.nextset():
                pass
            
            cursor.close()
            
            results = []
            for row in rows:
                # Parse project_ids from comma-separated string
                project_ids_str = row[9] if row[9] else ''
                project_ids = [int(pid) for pid in project_ids_str.split(',') if pid]
                
                results.append({
                    'id':                   row[0],
                    'user_id':              row[1],
                    'title':                row[2],
                    'summary':              row[3],
                    'created_at':           row[4],
                    'updated_at':           row[5],
                    'is_active':            row[6],
                    'last_message_preview': row[7],
                    'added_to_project_at':  row[8],
                    'project_ids':          project_ids,
                })
            
            return results
            
        except Exception as e:
            cursor.close()
            error_msg = str(e)
            if 'access denied' in error_msg.lower() or 'not found' in error_msg.lower():
                raise PermissionError("Project not found or access denied")
            raise
