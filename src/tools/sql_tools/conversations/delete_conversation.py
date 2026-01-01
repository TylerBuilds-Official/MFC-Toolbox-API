from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def delete_conversation(conversation_id: int, user_id: int) -> bool:
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE {SCHEMA}.Conversations "
                       f"SET IsActive = 0, UpdatedAt = GETDATE() "
                       f" WHERE Id = ? AND UserId = ? AND IsActive = 1",
                       (conversation_id, user_id))

        affected = cursor.rowcount
        cursor.close()

        return affected > 0
