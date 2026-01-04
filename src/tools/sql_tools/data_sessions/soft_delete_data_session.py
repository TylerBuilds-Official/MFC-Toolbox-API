"""
Soft deletes a data session by setting IsActive = 0.
"""
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def soft_delete_data_session(session_id: int, user_id: int) -> bool:
    """
    Args:
        session_id: The session ID to delete
        user_id: The user ID (for ownership verification)
        
    Returns:
        True if delete succeeded, False if session not found or not owned by user.
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            UPDATE {SCHEMA}.DataSessions
            SET IsActive = 0, UpdatedAt = GETDATE()
            WHERE Id = ? AND UserId = ? AND IsActive = 1
            """,
            (session_id, user_id)
        )
        rows_affected = cursor.rowcount
        cursor.close()
        
        return rows_affected > 0
