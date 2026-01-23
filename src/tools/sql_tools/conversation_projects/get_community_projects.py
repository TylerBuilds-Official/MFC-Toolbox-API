"""
Gets all shared_open (community) projects with user's relationship status.

Returns all open projects showing whether user is owner, member, or can join.
"""
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_community_projects(user_id: int) -> list[dict]:
    """
    Gets all shared_open projects with the user's relationship status.
    
    Calls Toolbox_GetCommunityProjects stored procedure.
    
    Args:
        user_id: The current user's ID
        
    Returns:
        List of project dicts with user_status field:
        - 'owner': user owns this project
        - 'member': user has joined this project
        - 'available': user can join this project
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"EXEC {SCHEMA}.Toolbox_GetCommunityProjects @UserId = ?",
            (user_id,)
        )
        
        rows = cursor.fetchall()
        
        # Consume any additional result sets
        while cursor.nextset():
            pass
        
        cursor.close()
        
        return [
            {
                'id':                 row[0],
                'name':               row[1],
                'description':        row[2],
                'color':              row[3],
                'owner_name':         row[4],
                'owner_email':        row[5],
                'member_count':       row[6],
                'conversation_count': row[7],
                'created_at':         row[8],
                'user_status':        row[9],  # 'owner', 'member', or 'available'
            }
            for row in rows
        ]
