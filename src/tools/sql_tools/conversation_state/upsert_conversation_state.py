from src.tools.sql_tools.mssql_pool import get_mssql_connection, SCHEMA


def upsert_conversation_state(conversation_id: int, state_json: str, turn_count: int) -> bool:
    """
    Insert or update the state for a conversation.
    
    Args:
        conversation_id: The conversation's ID
        state_json: Serialized state JSON string
        turn_count: Current turn count
        
    Returns:
        True if successful
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        # SQL Server MERGE for upsert
        cursor.execute(
            f"""
            MERGE {SCHEMA}.ConversationState AS target
            USING (SELECT ? AS ConversationId, ? AS StateJson, ? AS TurnCount) AS source
            ON target.ConversationId = source.ConversationId
            WHEN MATCHED THEN
                UPDATE SET 
                    StateJson = source.StateJson,
                    TurnCount = source.TurnCount,
                    UpdatedAt = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (ConversationId, StateJson, TurnCount, UpdatedAt)
                VALUES (source.ConversationId, source.StateJson, source.TurnCount, GETDATE());
            """,
            (conversation_id, state_json, turn_count)
        )
        
        cursor.close()
        return True
