from src.tools.sql_tools.mssql_pool import SCHEMA, get_mssql_connection


def update_conversation_summary(conversation_id: int, summary: str) -> None:
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE {SCHEMA}.Conversations "
            f"SET Summary = ?, "
            f"UpdatedAt = GETDATE() "
            f"WHERE Id = ?",
            (summary, conversation_id))
        cursor.close()