from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def create_chat_file(
        file_id: str,
        user_id: int,
        original_name: str,
        stored_name: str,
        category: str,
        mime_type: str,
        file_size: int,
        storage_path: str ) -> dict:
    """Insert a new chat file record."""

    with get_mssql_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            f"INSERT INTO {SCHEMA}.ChatFiles "
            f"(Id, UserId, OriginalName, StoredName, Category, MimeType, FileSize, StoragePath) "
            f"OUTPUT INSERTED.Id, INSERTED.UserId, INSERTED.MessageId, "
            f"INSERTED.OriginalName, INSERTED.StoredName, INSERTED.Category, "
            f"INSERTED.MimeType, INSERTED.FileSize, INSERTED.StoragePath, INSERTED.CreatedAt "
            f"VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (file_id, user_id, original_name, stored_name, category, mime_type, file_size, storage_path)
        )

        row = cursor.fetchone()
        cursor.close()

        return {
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
