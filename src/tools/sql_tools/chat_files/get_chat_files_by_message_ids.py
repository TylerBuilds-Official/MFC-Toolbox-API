from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_chat_files_by_message_ids(message_ids: list[int]) -> dict[int, list[dict]]:
    """Batch-fetch all files for a list of message IDs. Returns {message_id: [file_dicts]}."""

    if not message_ids:

        return {}

    placeholders = ",".join(["?"] * len(message_ids))

    with get_mssql_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            f"SELECT Id, UserId, MessageId, OriginalName, StoredName, "
            f"Category, MimeType, FileSize, StoragePath, CreatedAt "
            f"FROM {SCHEMA}.ChatFiles WHERE MessageId IN ({placeholders})",
            message_ids
        )

        rows   = cursor.fetchall()
        cursor.close()

        result: dict[int, list[dict]] = {}
        for row in rows:
            msg_id = row[2]
            file_dict = {
                "id":            str(row[0]),
                "user_id":       row[1],
                "message_id":    msg_id,
                "original_name": row[3],
                "stored_name":   row[4],
                "category":      row[5],
                "mime_type":     row[6],
                "file_size":     row[7],
                "storage_path":  row[8],
                "created_at":    str(row[9]),
            }
            result.setdefault(msg_id, []).append(file_dict)

        return result
