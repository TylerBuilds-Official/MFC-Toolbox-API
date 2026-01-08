from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def search_memories(user_id: int, query: str, limit: int = 10, track_reference: bool = True) -> list[dict]:
    """
    Search user's memories by keyword using LIKE.
    Updates LastReferencedAt and ReferenceCount for returned results.
    
    Args:
        user_id: The user's ID
        query: Search keywords
        limit: Maximum number of results
        track_reference: If True, updates reference tracking (default True)
        
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
                IsActive,
                LastReferencedAt,
                ReferenceCount,
                ExpiresAt
            FROM {SCHEMA}.UserMemories
            WHERE UserId = ? 
              AND IsActive = 1
              AND Content LIKE ?
              AND (ExpiresAt IS NULL OR ExpiresAt > GETUTCDATE())
            ORDER BY ReferenceCount DESC, CreatedAt DESC
            """,
            (limit, user_id, search_pattern)
        )
        
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        
        results = [dict(zip(columns, row)) for row in rows]
        
        # Update reference tracking for found memories
        if track_reference and results:
            memory_ids = [r['Id'] for r in results]
            placeholders = ','.join(['?' for _ in memory_ids])
            cursor.execute(
                f"""
                UPDATE {SCHEMA}.UserMemories
                SET LastReferencedAt = GETUTCDATE(),
                    ReferenceCount = ReferenceCount + 1
                WHERE Id IN ({placeholders})
                """,
                memory_ids
            )
        
        cursor.close()
        
        return results
