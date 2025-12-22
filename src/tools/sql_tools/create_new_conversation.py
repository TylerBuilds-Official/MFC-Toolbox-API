from src.tools.sql_tools import get_mssql_connection
from src.tools.sql_tools.mssql_pool import SCHEMA


def create_new_conversation(user_id: int, title: str = "New Conversation") -> dict:
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"INSERT INTO {SCHEMA}.Conversations (UserId, Title, Summary, IsActive, LastMessagePreview) "
            f"OUTPUT INSERTED.Id, INSERTED.UserId, INSERTED.Title, INSERTED.Summary, "
            f"INSERTED.CreatedAt, INSERTED.UpdatedAt, INSERTED.IsActive, INSERTED.LastMessagePreview "
            f"VALUES (?, ? , '', 1, '')",
            (user_id, title))
        new_row = cursor.fetchone()
        cursor.close()

        return {
            'id':                   new_row[0],
            'user_id':              new_row[1],
            'title':                new_row[2],
            'summary':              new_row[3],
            'created_at':           new_row[4],
            'updated_at':           new_row[5],
            'is_active':            new_row[6],
            'last_message_preview': new_row[7]
        }
