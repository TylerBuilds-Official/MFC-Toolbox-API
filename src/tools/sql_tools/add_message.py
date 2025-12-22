from src.tools.sql_tools.mssql_pool import get_mssql_connection, SCHEMA

def add_message(conversation_id: int, role: str, content: str,
                model: str, provider: str, tokens_used: int = None) -> dict:
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"INSERT INTO {SCHEMA}.Messages "
            f"(ConversationId, Role, Content, Model, Provider, TokensUsed) "
            f"OUTPUT INSERTED.Id, INSERTED.ConversationId, INSERTED.Role,"
            f" INSERTED.Content, INSERTED.Model, INSERTED.Provider,"
            f" INSERTED.TokensUsed, INSERTED.CreatedAt "
            f"VALUES (?, ?, ?, ?, ?, ?)",
            (conversation_id, role, content, model, provider, tokens_used))
        row = cursor.fetchone()

        cursor.execute(
            f"UPDATE {SCHEMA}.Conversations "
            f"SET UpdatedAt = GETDATE() "
            f"WHERE Id = ?",
            (conversation_id,))

        cursor.close()
        return {
            'id': row[0],
            'conversation_id': row[1],
            'role': row[2],
            'content': row[3],
            'model': row[4],
            'provider': row[5],
            'tokens_used': row[6],
            'created_at': row[7]
        }