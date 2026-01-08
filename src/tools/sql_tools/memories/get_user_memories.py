from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_user_memories(user_id: int, limit: int = 15) -> list[dict]:
    """
    Get active memories for a user, ordered by most recent first.
    Used for system prompt injection.
    Does NOT update reference tracking (passive load).
    
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
                IsActive,
                LastReferencedAt,
                ReferenceCount,
                ExpiresAt
            FROM {SCHEMA}.UserMemories
            WHERE UserId = ? 
              AND IsActive = 1
              AND (ExpiresAt IS NULL OR ExpiresAt > GETUTCDATE())
            ORDER BY CreatedAt DESC
            """,
            (limit, user_id)
        )
        
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        
        return [dict(zip(columns, row)) for row in rows]


def get_all_memories(
    user_id: int, 
    memory_type: str = None, 
    include_inactive: bool = False,
    include_expired: bool = False
) -> list[dict]:
    """
    Get all memories for a user with optional filters.
    Used for UI memory management.
    
    Args:
        user_id: The user's ID
        memory_type: Filter by type (optional)
        include_inactive: Include soft-deleted memories
        include_expired: Include expired memories
        
    Returns:
        List of memory dictionaries
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        conditions = ["UserId = ?"]
        params = [user_id]
        
        if not include_inactive:
            conditions.append("IsActive = 1")
        
        if not include_expired:
            conditions.append("(ExpiresAt IS NULL OR ExpiresAt > GETUTCDATE())")
        
        if memory_type:
            conditions.append("MemoryType = ?")
            params.append(memory_type)
        
        where_clause = " AND ".join(conditions)
        
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
                IsActive,
                LastReferencedAt,
                ReferenceCount,
                ExpiresAt
            FROM {SCHEMA}.UserMemories
            WHERE {where_clause}
            ORDER BY CreatedAt DESC
            """,
            params
        )
        
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        
        return [dict(zip(columns, row)) for row in rows]


def get_stale_memories(user_id: int, days: int = 90) -> list[dict]:
    """
    Get memories that haven't been referenced in X days.
    Used for stale memory review in UI.
    
    Args:
        user_id: The user's ID
        days: Number of days without reference to consider stale
        
    Returns:
        List of stale memory dictionaries
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
                IsActive,
                LastReferencedAt,
                ReferenceCount,
                ExpiresAt
            FROM {SCHEMA}.UserMemories
            WHERE UserId = ? 
              AND IsActive = 1
              AND (ExpiresAt IS NULL OR ExpiresAt > GETUTCDATE())
              AND (
                (LastReferencedAt IS NULL AND DATEDIFF(day, CreatedAt, GETUTCDATE()) > ?)
                OR DATEDIFF(day, LastReferencedAt, GETUTCDATE()) > ?
              )
            ORDER BY 
                COALESCE(LastReferencedAt, CreatedAt) ASC
            """,
            (user_id, days, days)
        )
        
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        
        return [dict(zip(columns, row)) for row in rows]
