from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_conversation_state(conversation_id: int) -> dict | None:
    """
    Get the persisted state for a conversation.
    
    Args:
        conversation_id: The conversation's ID
        
    Returns:
        Dict with state_json, turn_count, updated_at or None if not found
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT 
                ConversationId,
                StateJson,
                TurnCount,
                UpdatedAt
            FROM {SCHEMA}.ConversationState
            WHERE ConversationId = ?
            """,
            (conversation_id,)
        )
        
        row = cursor.fetchone()
        cursor.close()
        
        if row is None:
            return None
        
        return {
            "conversation_id": row[0],
            "state_json": row[1],
            "turn_count": row[2],
            "updated_at": row[3]
        }
