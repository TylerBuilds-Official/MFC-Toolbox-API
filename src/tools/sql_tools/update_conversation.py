from src.tools.sql_tools import get_mssql_connection
from src.tools.sql_tools.mssql_pool import SCHEMA


def update_conversation(conversation_id: int, user_id: int, updates: dict) -> bool:
    allowed_fields = {"title": "Title",
                      "summary": "Summary",
                      "last_message_preview": "LastMessagePreview"}
    set_clauses = []
    params = []

    for key, column in allowed_fields.items():
        if key in updates:
            set_clauses.append(f'{column} = ?')
            params.append(updates[key])

    if not set_clauses:
        return False

    set_clauses.append("UpdatedAt = GETDATE()")
    params.append(conversation_id)
    params.append(user_id)



    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        query = (
            f"UPDATE {SCHEMA}.Conversations "
            f"SET {', '.join(set_clauses)} "
            f"WHERE Id = ? AND UserId = ?")

        cursor.execute(query, tuple(params))

        if cursor.rowcount == 0:
            cursor.close()
            return False
        cursor.close()
    return True