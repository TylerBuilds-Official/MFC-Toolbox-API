"""
Gets pending project invites for a user.
"""
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_pending_invites(user_email: str) -> list[dict]:
    """
    Gets all pending project invites for a user by their email.
    
    Calls Toolbox_GetPendingInvites stored procedure.
    Also expires old invites automatically.
    
    Args:
        user_email: The user's email address
        
    Returns:
        List of invite dicts with project info and inviter details
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"EXEC {SCHEMA}.Toolbox_GetPendingInvites @UserEmail = ?",
            (user_email,)
        )
        
        rows = cursor.fetchall()
        
        # Consume any additional result sets
        while cursor.nextset():
            pass
        
        cursor.close()
        
        return [
            {
                'id':                  row[0],
                'project_id':          row[1],
                'project_name':        row[2],
                'project_description': row[3],
                'project_color':       row[4],
                'project_type':        row[5],
                'invited_by_name':     row[6],
                'invited_by_email':    row[7],
                'created_at':          row[8],
                'expires_at':          row[9],
            }
            for row in rows
        ]
