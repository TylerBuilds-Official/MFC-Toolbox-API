from src.tools.sql_tools.mssql_pool import get_mssql_connection, SCHEMA

def admin_delete_messages_for_conversation(conversation_id: int) -> int:
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {SCHEMA}.Messages "
                       f"WHERE ConversationId = ?",
                       (conversation_id,))
        affected_rows = cursor.rowcount
        cursor.close()
        return affected_rows