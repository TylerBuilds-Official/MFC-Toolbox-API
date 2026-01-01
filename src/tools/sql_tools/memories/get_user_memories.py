from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_user_memories(user_id: int, limit: int = 15) -> list[dict]:
    """
    Get active memories for a user, ordered by most recent first.
    Used for system prompt injection.
    
    Args:
        user_id: The user's ID
        limit: Maximum number of memories to return
        
    Returns:
        List of memory dictionaries
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT TOP (?)
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
            WHERE UserId = ? AND IsActive = 1
            ORDER BY CreatedAt DESC
            """,
            (limit, user_id)
        )
        
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        
        return [dict(zip(columns, row)) for row in rows]
