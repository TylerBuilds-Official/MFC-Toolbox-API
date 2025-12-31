from src.tools.sql_tools.mssql_pool import get_mssql_connection, SCHEMA


def get_memory(memory_id: int, user_id: int) -> dict | None:
    """
    Get a single memory by ID.
    Validates ownership via user_id.
    
    Args:
        memory_id: The memory's ID
        user_id: The user's ID (for ownership validation)
        
    Returns:
        Memory dictionary or None if not found
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT
                Id,
                UserId,
                MemoryType,
                Content,
                SourceConversationId,
                SourceMessageId,
                CreatedAt,
                UpdatedAt,
                IsActive
            FROM {SCHEMA}.UserMemories
            WHERE Id = ? AND UserId = ?
            """,
            (memory_id, user_id)
        )
        
        row = cursor.fetchone()
        cursor.close()
        
        if row is None:
            return None
        
        columns = [column[0] for column in cursor.description]
        return dict(zip(columns, row))
