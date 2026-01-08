"""
Removes a member from a project.
"""
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def remove_project_member(
    project_id: int,
    member_user_id: int,
    requested_by: int
) -> bool:
    """
    Removes a member from a project.
    
    Calls Toolbox_RemoveProjectMember stored procedure.
    
    Only the owner can remove members, or a member can remove themselves.
    Cannot remove the project owner.
    
    Args:
        project_id: The project ID
        member_user_id: User ID of the member to remove
        requested_by: User ID of the person making the request
        
    Returns:
        True if removal succeeded
        
    Raises:
        PermissionError: If requester doesn't have permission
        ValueError: If trying to remove the owner
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                f"EXEC {SCHEMA}.Toolbox_RemoveProjectMember "
                f"@ProjectId = ?, @MemberUserId = ?, @RequestedBy = ?",
                (project_id, member_user_id, requested_by)
            )
            
            row = cursor.fetchone()
            
            # Consume any additional result sets
            while cursor.nextset():
                pass
            
            cursor.close()
            
            return row is not None and row[0] > 0
            
        except Exception as e:
            cursor.close()
            error_msg = str(e)
            if 'Only the project owner' in error_msg:
                raise PermissionError(error_msg)
            if 'Cannot remove the project owner' in error_msg:
                raise ValueError(error_msg)
            raise
