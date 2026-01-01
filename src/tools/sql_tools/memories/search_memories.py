from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def search_memories(user_id: int, query: str, limit: int = 10) -> list[dict]:
    """
    Search user's memories by keyword using LIKE.
    Used by the MCP search tool.
    
    Args:
        user_id: The user's ID
        query: Search keywords
        limit: Maximum number of results
        
    Returns:
        List of matching memory dictionaries
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        # Build LIKE pattern - search for each word
        search_pattern = f"%{query}%"
        
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
            WHERE UserId = ? 
              AND IsActive = 1
              AND Content LIKE ?
            ORDER BY CreatedAt DESC
            """,
            (limit, user_id, search_pattern)
        )
        
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        
        return [dict(zip(columns, row)) for row in rows]
