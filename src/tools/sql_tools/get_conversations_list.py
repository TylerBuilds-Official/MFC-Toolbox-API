from src.tools.sql_tools import get_mssql_connection
from src.tools.sql_tools.mssql_pool import SCHEMA

def get_conversations_list(user_id: int, include_inactive=False) -> list[tuple]:
    with get_mssql_connection() as conn:
        cursor = conn.cursor()

        if include_inactive:
            cursor.execute(
                f"SELECT Id, UserId, Title, Summary, CreatedAt, UpdatedAt, IsActive, LastMessagePreview "
                f"FROM {SCHEMA}.Conversations "
                f"WHERE UserId = ? "
                f"ORDER BY UpdatedAt DESC",
                (user_id,))
        else:
            cursor.execute(
                f"SELECT Id, UserId, Title, Summary, CreatedAt, UpdatedAt, IsActive, LastMessagePreview "
                f"FROM {SCHEMA}.Conversations "
                f"WHERE UserId = ? AND IsActive = 1 "
                f"ORDER BY UpdatedAt DESC",
                (user_id,))

        rows = cursor.fetchall()
        cursor.close()

        return [
            {
                'id': row[0],
                'user_id': row[1],
                'title': row[2],
                'summary': row[3],
                'created_at': row[4],
                'updated_at': row[5],
                'is_active': row[6],
                'last_message_preview': row[7]
            }
            for row in rows
        ]