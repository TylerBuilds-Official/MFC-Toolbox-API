from src.tools.sql_tools.mssql_pool import get_mssql_connection, SCHEMA


def get_message(message_id: int) -> dict | None:
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT Id, ConversationId,"
            f"Role, Content, Model, "
            f"Provider, TokensUsed, CreatedAt "
            f"FROM {SCHEMA}.Messages "
            f"WHERE Id = ?",
            (message_id,)
        )

        row = cursor.fetchone()
        cursor.close()

        if not row:
            return None

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