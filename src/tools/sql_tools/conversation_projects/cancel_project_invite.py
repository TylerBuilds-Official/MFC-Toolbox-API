"""
Cancels a pending project invite.
"""
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def cancel_project_invite(invite_id: int, user_id: int) -> bool:
    """
    Cancels a pending project invite.
    
    Only the project owner can cancel invites.
    Calls Toolbox_CancelProjectInvite stored procedure.
    
    Args:
        invite_id: The invite ID to cancel
        user_id: User ID for ownership verification
        
    Returns:
        True if cancellation succeeded
        
    Raises:
        PermissionError: If user is not the project owner
        ValueError: If invite is not pending
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                f"EXEC {SCHEMA}.Toolbox_CancelProjectInvite @InviteId = ?, @UserId = ?",
                (invite_id, user_id)
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
            if 'owner' in error_msg.lower():
                raise PermissionError(error_msg)
            if 'not pending' in error_msg.lower():
                raise ValueError(error_msg)
            raise
