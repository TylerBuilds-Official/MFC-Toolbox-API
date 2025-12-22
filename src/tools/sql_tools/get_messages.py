from src.tools.sql_tools.mssql_pool import get_mssql_connection, SCHEMA

def get_messages(conversation_id: int, limit: int = None):
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        if limit:
            cursor.execute(
                f"SELECT TOP (?) Id, ConversationId, "
                f"Role, Content, Model, Provider, "
                f"TokensUsed, CreatedAt "
                f"FROM {SCHEMA}.Messages "
                f"WHERE ConversationId = ? "
                f"ORDER BY CreatedAt ASC",
                (limit, conversation_id)
            )
        else:
            cursor.execute(
                f"SELECT Id, ConversationId, "
                f"Role, Content, Model, Provider, "
                f"TokensUsed, CreatedAt "
                f"FROM {SCHEMA}.Messages "
                f"WHERE ConversationId = ? "
                f"ORDER BY CreatedAt ASC",
                (conversation_id,)
            )

        rows = cursor.fetchall()
        cursor.close()

        return [{
            'id': row[0],
            'conversation_id': row[1],
            'role': row[2],
            'content': row[3],
            'model': row[4],
            'provider': row[5],
            'tokens_used': row[6],
            'created_at': row[7]
        }
        for row in rows]