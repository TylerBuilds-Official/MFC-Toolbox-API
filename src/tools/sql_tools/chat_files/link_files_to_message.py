from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def link_files_to_message(file_ids: list[str], message_id: int) -> int:
    """Link uploaded files to a message. Returns count of updated rows."""

    if not file_ids:

        return 0

    placeholders = ",".join(["?"] * len(file_ids))

    with get_mssql_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            f"UPDATE {SCHEMA}.ChatFiles "
            f"SET MessageId = ? "
            f"WHERE Id IN ({placeholders})",
            [message_id] + file_ids
        )

        updated = cursor.rowcount
        cursor.close()

        return updated
