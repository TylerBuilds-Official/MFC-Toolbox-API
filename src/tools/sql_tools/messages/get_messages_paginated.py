from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_messages_paginated(conversation_id: int, limit: int = 50, before_id: int = None) -> dict:
    """
    Get messages for a conversation with cursor-based pagination.
    Returns newest messages first (descending by ID), but the returned list
    is reversed to maintain chronological order for display.
    
    Args:
        conversation_id: The conversation to fetch messages from
        limit: Maximum number of messages to return (default 50)
        before_id: If provided, only return messages with ID < this value (for pagination)
    
    Returns:
        dict with:
            - messages: List of message dicts in chronological order (oldest first)
            - has_more: Boolean indicating if there are older messages
            - oldest_id: The ID of the oldest message returned (use as next cursor)
            - total_count: Total number of messages in conversation
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        # Get total count for this conversation
        cursor.execute(
            f"SELECT COUNT(*) FROM {SCHEMA}.Messages WHERE ConversationId = ?",
            (conversation_id,)
        )
        total_count = cursor.fetchone()[0]
        
        # Build the main query - fetch limit + 1 to check if there's more
        if before_id:
            cursor.execute(
                f"""
                SELECT TOP (?) Id, ConversationId, Role, Content, Model, Provider,
                       TokensUsed, CreatedAt, UserId, Thinking, ContentBlocks
                FROM {SCHEMA}.Messages
                WHERE ConversationId = ? AND Id < ?
                ORDER BY Id DESC
                """,
                (limit + 1, conversation_id, before_id)
            )
        else:
            cursor.execute(
                f"""
                SELECT TOP (?) Id, ConversationId, Role, Content, Model, Provider,
                       TokensUsed, CreatedAt, UserId, Thinking, ContentBlocks
                FROM {SCHEMA}.Messages
                WHERE ConversationId = ?
                ORDER BY Id DESC
                """,
                (limit + 1, conversation_id)
            )
        
        rows = cursor.fetchall()
        cursor.close()
        
        # Check if there are more messages
        has_more = len(rows) > limit
        
        # Trim to actual limit
        if has_more:
            rows = rows[:limit]
        
        # Build message list (still in descending order at this point)
        messages = [{
            'id': row[0],
            'conversation_id': row[1],
            'role': row[2],
            'content': row[3],
            'model': row[4],
            'provider': row[5],
            'tokens_used': row[6],
            'created_at': row[7],
            'user_id': row[8],
            'thinking': row[9],
            'content_blocks': row[10]
        } for row in rows]
        
        # Get oldest_id before reversing
        oldest_id = messages[-1]['id'] if messages else None
        
        # Reverse to chronological order (oldest first) for display
        messages.reverse()
        
        return {
            'messages': messages,
            'has_more': has_more,
            'oldest_id': oldest_id,
            'total_count': total_count
        }
