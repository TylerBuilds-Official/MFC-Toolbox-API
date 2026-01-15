from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_recent_exchanges(conversation_id: int, limit: int = 4):
    """Fetch the most recent exchanges from a conversation for context."""
    if not conversation_id:
        return []
    
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"EXEC {SCHEMA}.Toolbox_GetRecentExchanges ?, ?",
            (conversation_id, limit)
        )
        rows = cursor.fetchall()
        cursor.close()

        return [{
            'role': row[0],
            'content': row[1],
            'created_at': row[2]
        } for row in rows]