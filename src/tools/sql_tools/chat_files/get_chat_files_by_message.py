from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_chat_files_by_message(message_id: int) -> list[dict]:
    """Get all files attached to a specific message."""

    with get_mssql_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            f"SELECT Id, UserId, MessageId, OriginalName, StoredName, "
            f"Category, MimeType, FileSize, StoragePath, CreatedAt "
            f"FROM {SCHEMA}.ChatFiles WHERE MessageId = ?",
            (message_id,)
        )

        rows   = cursor.fetchall()
        cursor.close()

        return [
            {
                "id":            str(row[0]),
                "user_id":       row[1],
                "message_id":    row[2],
                "original_name": row[3],
                "stored_name":   row[4],
                "category":      row[5],
                "mime_type":     row[6],
                "file_size":     row[7],
                "storage_path":  row[8],
                "created_at":    str(row[9]),
            }
            for row in rows
        ]
