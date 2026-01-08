"""
Accepts a project invite.
"""
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def accept_project_invite(
    invite_id: int,
    user_id: int,
    user_email: str
) -> dict:
    """
    Accepts a project invite.
    
    Calls Toolbox_AcceptProjectInvite stored procedure.
    
    Args:
        invite_id: The invite ID
        user_id: The accepting user's ID
        user_email: The accepting user's email (must match invite)
        
    Returns:
        Dict with 'project_id' and 'message' keys
        
    Raises:
        ValueError: If invite not found, expired, or email mismatch
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                f"EXEC {SCHEMA}.Toolbox_AcceptProjectInvite "
                f"@InviteId = ?, @UserId = ?, @UserEmail = ?",
                (invite_id, user_id, user_email)
            )
            
            row = cursor.fetchone()
            
            # Consume any additional result sets
            while cursor.nextset():
                pass
            
            cursor.close()
            
            if row:
                return {
                    'project_id': row[0],
                    'message':    row[1] if len(row) > 1 else 'Invite accepted'
                }
            
            return {'project_id': None, 'message': 'Unknown error'}
            
        except Exception as e:
            cursor.close()
            error_msg = str(e)
            if 'not found' in error_msg.lower() or 'expired' in error_msg.lower() or 'match' in error_msg.lower():
                raise ValueError(error_msg)
            raise
