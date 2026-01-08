from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def create_memory(
    user_id: int,
    content: str,
    memory_type: str = "fact",
    source_conversation_id: int = None,
    source_message_id: int = None,
    expires_at: str = None
) -> dict:
    """
    Create a new memory for a user.
    
    Args:
        user_id: The user's ID
        content: The memory content
        memory_type: Type of memory ('fact', 'preference', 'project', 'skill', 'context')
        source_conversation_id: Optional conversation this memory came from
        source_message_id: Optional message this memory came from
        expires_at: Optional expiration datetime (ISO format string)
        
    Returns:
        The created memory dictionary
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"""
            INSERT INTO {SCHEMA}.UserMemories 
                (UserId, MemoryType, Content, SourceConversationId, SourceMessageId, ExpiresAt)
            OUTPUT 
                INSERTED.Id,
                INSERTED.UserId,
                INSERTED.MemoryType,
                INSERTED.Content,
                INSERTED.SourceConversationId,
                INSERTED.SourceMessageId,
                INSERTED.CreatedAt,
                INSERTED.UpdatedAt,
                INSERTED.IsActive,
                INSERTED.LastReferencedAt,
                INSERTED.ReferenceCount,
                INSERTED.ExpiresAt
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, memory_type, content, source_conversation_id, source_message_id, expires_at)
        )
        
        row = cursor.fetchone()
        columns = [column[0] for column in cursor.description]
        cursor.close()
        
        return dict(zip(columns, row))
