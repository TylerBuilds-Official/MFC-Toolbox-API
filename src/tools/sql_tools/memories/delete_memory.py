from src.tools.sql_tools.mssql_pool import get_mssql_connection, SCHEMA


def delete_memory(memory_id: int, user_id: int) -> bool:
    """
    Soft delete a memory (sets IsActive = 0).
    
    Args:
        memory_id: The memory's ID
        user_id: The user's ID (for ownership validation)
        
    Returns:
        True if deleted, False if not found
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            UPDATE {SCHEMA}.UserMemories
            SET IsActive = 0, UpdatedAt = GETDATE()
            WHERE Id = ? AND UserId = ?
            """,
            (memory_id, user_id)
        )
        
        rows_affected = cursor.rowcount
        cursor.close()
        
        return rows_affected > 0
