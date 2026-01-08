"""
Invites a user to a project.
"""
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def invite_to_project(
    project_id: int,
    invited_email: str,
    invited_by: int,
    expires_in_days: int = 7
) -> dict:
    """
    Invites a user to a project by email.
    
    Calls Toolbox_InviteToProject stored procedure.
    
    Args:
        project_id: The project ID
        invited_email: Email address of user to invite
        invited_by: User ID of the person sending the invite
        expires_in_days: Days until invite expires (default 7)
        
    Returns:
        Dict with 'invite_id' and 'message' keys
        
    Raises:
        PermissionError: If inviter doesn't have permission
        ValueError: If project not found, is private, or user already a member
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                f"EXEC {SCHEMA}.Toolbox_InviteToProject "
                f"@ProjectId = ?, @InvitedEmail = ?, @InvitedBy = ?, @ExpiresInDays = ?",
                (project_id, invited_email, invited_by, expires_in_days)
            )
            
            row = cursor.fetchone()
            
            # Consume any additional result sets
            while cursor.nextset():
                pass
            
            cursor.close()
            
            if row:
                return {
                    'invite_id': row[0],
                    'message':   row[1] if len(row) > 1 else 'Invite sent'
                }
            
            return {'invite_id': None, 'message': 'Unknown error'}
            
        except Exception as e:
            cursor.close()
            error_msg = str(e)
            if 'permission' in error_msg.lower():
                raise PermissionError(error_msg)
            if 'not found' in error_msg.lower() or 'private' in error_msg.lower() or 'already' in error_msg.lower():
                raise ValueError(error_msg)
            raise
