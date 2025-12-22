from src.tools.sql_tools.mssql_pool import get_mssql_connection, SCHEMA


def add_message(conversation_id: int, role: str, content: str,
                model: str, provider: str, tokens_used: int = None, user_id: int = None) -> dict:
    
    print(f"[add_message] conversation_id={conversation_id} (type={type(conversation_id).__name__})")
    print(f"[add_message] user_id={user_id} (type={type(user_id).__name__})")
    
    if user_id is None:
        raise ValueError("user_id is required for all messages")

    conversation_id = int(conversation_id)

    with get_mssql_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            f"INSERT INTO {SCHEMA}.Messages "
            f"(ConversationId, Role, Content, Model, Provider, TokensUsed, UserId) "
            f"OUTPUT INSERTED.Id, INSERTED.ConversationId, INSERTED.Role, "
            f"INSERTED.Content, INSERTED.Model, INSERTED.Provider, "
            f"INSERTED.TokensUsed, INSERTED.CreatedAt, INSERTED.UserId "
            f"VALUES (?, ?, ?, ?, ?, ?, ?)",
            (conversation_id, role, content, model, provider, tokens_used, user_id))

        row = cursor.fetchone()

        preview_prefix = "You: " if role == "user" else ""
        preview_content = content[:100] + "..." if len(content) > 100 else content
        preview = f"{preview_prefix}{preview_content}"


        cursor.execute(
            f"UPDATE {SCHEMA}.Conversations "
            f"SET LastMessagePreview = ?, UpdatedAt = GETDATE() "
            f"WHERE Id = ?",
            (preview, conversation_id))

        cursor.close()

        return {
            'id': row[0],
            'conversation_id': row[1],
            'role': row[2],
            'content': row[3],
            'model': row[4],
            'provider': row[5],
            'tokens_used': row[6],
            'created_at': row[7],
            'user_id': row[8]
        }