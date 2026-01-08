"""
Declines a project invite.
"""
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def decline_project_invite(invite_id: int, user_email: str) -> bool:
    """
    Declines a project invite.
    
    Calls Toolbox_DeclineProjectInvite stored procedure.
    
    Args:
        invite_id: The invite ID
        user_email: The user's email (must match invite)
        
    Returns:
        True if decline succeeded
        
    Raises:
        ValueError: If invite not found or already responded
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                f"EXEC {SCHEMA}.Toolbox_DeclineProjectInvite "
                f"@InviteId = ?, @UserEmail = ?",
                (invite_id, user_email)
            )
            
            row = cursor.fetchone()
            
            # Consume any additional result sets
            while cursor.nextset():
                pass
            
            cursor.close()
            
            return row is not None and row[0] == 1
            
        except Exception as e:
            cursor.close()
            error_msg = str(e)
            if 'not found' in error_msg.lower() or 'already' in error_msg.lower():
                raise ValueError(error_msg)
            raise
