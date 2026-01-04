"""
Links orphaned artifacts to a message after both are created.
"""
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def link_artifacts_to_message(conversation_id: int, message_id: int, seconds_ago: int = 60) -> list[str]:
    """
    Finds artifacts in a conversation that have no MessageId and were created recently,
    then links them to the specified message.
    
    This handles the timing issue where artifacts are created during tool execution
    but the assistant message doesn't exist yet.
    
    Args:
        conversation_id: The conversation to search
        message_id: The message ID to link artifacts to
        seconds_ago: How far back to look for orphaned artifacts (default 60s)
        
    Returns:
        List of artifact IDs that were linked
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        # Find and update orphaned artifacts, returning their IDs
        cursor.execute(
            f"""
            UPDATE {SCHEMA}.ChatArtifacts
            SET MessageId = ?, UpdatedAt = GETDATE()
            OUTPUT INSERTED.Id
            WHERE ConversationId = ?
              AND MessageId IS NULL
              AND CreatedAt >= DATEADD(SECOND, -?, GETDATE())
            """,
            (message_id, conversation_id, seconds_ago)
        )
        
        rows = cursor.fetchall()
        cursor.close()
        
        # Convert UUID rows to string list
        return [str(row[0]) for row in rows]
