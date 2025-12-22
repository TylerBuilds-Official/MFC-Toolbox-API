from src.tools.sql_tools import get_mssql_connection
from src.tools.sql_tools.mssql_pool import SCHEMA


def get_conversation(conversation_id: int, user_id: int):
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT Id, UserId, Title, Summary, CreatedAt, UpdatedAt, IsActive, LastMessagePreview "
                       f"FROM {SCHEMA}.Conversations "
                       f"WHERE Id = ? AND UserId = ?",
                       (conversation_id, user_id))

        row = cursor.fetchone()
        cursor.close()

        if not row:
            return None

        return {
            'id':                       row[0],
            'user_id':                  row[1],
            'title':                    row[2],
            'summary':                  row[3],
            'created_at':               row[4],
            'updated_at':               row[5],
            'is_active':                row[6],
            'last_message_preview':     row[7]
        }