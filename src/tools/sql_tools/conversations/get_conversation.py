from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_conversation(conversation_id: int, user_id: int):
    """
    Get a conversation if user has access.
    
    Access is granted if:
    1. User owns the conversation directly, OR
    2. User is a member of a project that contains this conversation
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        # Check ownership OR project membership
        query = f"""
            SELECT c.Id, c.UserId, c.Title, c.Summary, c.CreatedAt, c.UpdatedAt, c.IsActive, c.LastMessagePreview
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
        """
        
        cursor.execute(query, (conversation_id, user_id, user_id))
        row = cursor.fetchone()
        cursor.close()

        if not row:
            return None

        return {
            'id':                   row[0],
            'user_id':              row[1],
            'title':                row[2],
            'summary':              row[3],
            'created_at':           row[4],
            'updated_at':           row[5],
            'is_active':            row[6],
            'last_message_preview': row[7]
        }
