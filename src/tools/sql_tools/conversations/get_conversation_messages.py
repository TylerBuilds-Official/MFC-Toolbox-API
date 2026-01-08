from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_conversation_messages(conversation_id: int, user_id: int) -> dict | None:
    """
    Get all messages for a conversation, with access verification.
    
    Access is granted if:
    1. User owns the conversation directly, OR
    2. User is a member of a project that contains this conversation
    
    Args:
        conversation_id: The conversation to fetch messages for
        user_id: The requesting user's ID (access check)
        
    Returns:
        Dict with conversation metadata and messages, or None if not found/no access
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        # Verify access (ownership OR project membership) and get conversation metadata
        cursor.execute(
            f"""
            SELECT c.Id, c.Title, c.Summary, c.CreatedAt, c.UpdatedAt
            FROM {SCHEMA}.Conversations c
            WHERE c.Id = ? 
              AND c.IsActive = 1
              AND (
                c.UserId = ?
                OR EXISTS (
                  SELECT 1
                  FROM {SCHEMA}.ConversationProjectMemberships cpc
                  JOIN {SCHEMA}.ConversationProjectMembers cpm ON cpc.ProjectId = cpm.ProjectId
                  WHERE cpc.ConversationId = c.Id
                    AND cpm.UserId = ?
                )
              )
            """,
            (conversation_id, user_id, user_id)
        )
        
        conv_row = cursor.fetchone()
        if conv_row is None:
            cursor.close()
            return None
        
        conversation = {
            "id": conv_row[0],
            "title": conv_row[1],
            "summary": conv_row[2],
            "created_at": conv_row[3].isoformat() if conv_row[3] else None,
            "updated_at": conv_row[4].isoformat() if conv_row[4] else None,
        }
        
        # Fetch all messages in chronological order
        cursor.execute(
            f"""
            SELECT 
                Id,
                Role,
                Content,
                Model,
                Provider,
                CreatedAt,
                Thinking
            FROM {SCHEMA}.Messages
            WHERE ConversationId = ?
            ORDER BY CreatedAt ASC
            """,
            (conversation_id,)
        )
        
        messages = []
        for row in cursor.fetchall():
            msg = {
                "id": row[0],
                "role": row[1],
                "content": row[2],
                "model": row[3],
                "provider": row[4],
                "created_at": row[5].isoformat() if row[5] else None,
            }
            # Only include thinking if present
            if row[6]:
                msg["thinking"] = row[6]
            messages.append(msg)
        
        cursor.close()
        
        return {
            "conversation": conversation,
            "messages": messages,
            "message_count": len(messages)
        }
