from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_chat_file(file_id: str) -> dict | None:
    """Get a single chat file by ID."""

    with get_mssql_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            f"SELECT Id, UserId, MessageId, OriginalName, StoredName, "
            f"Category, MimeType, FileSize, StoragePath, CreatedAt "
            f"FROM {SCHEMA}.ChatFiles WHERE Id = ?",
            (file_id,)
        )

        row = cursor.fetchone()
        cursor.close()

        if not row:

            return None

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


def get_chat_files_by_ids(file_ids: list[str]) -> list[dict]:
    """Get multiple chat files by their IDs."""

    if not file_ids:

        return []

    placeholders = ",".join(["?"] * len(file_ids))

    with get_mssql_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            f"SELECT Id, UserId, MessageId, OriginalName, StoredName, "
            f"Category, MimeType, FileSize, StoragePath, CreatedAt "
            f"FROM {SCHEMA}.ChatFiles WHERE Id IN ({placeholders})",
            file_ids
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
