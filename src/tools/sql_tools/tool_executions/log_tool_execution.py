from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def log_tool_execution(
        tool_name:   str,
        user_id:     int | None = None,
        status:      str        = "success",
        duration_ms: int | None = None,
) -> None:
    """Log a tool execution to the ToolExecutions table. Fire-and-forget."""

    try:
        with get_mssql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"INSERT INTO {SCHEMA}.ToolExecutions (ToolName, UserId, Status, DurationMs) "
                f"VALUES (?, ?, ?, ?)",
                (tool_name, user_id, status, duration_ms)
            )
            conn.commit()
            cursor.close()
    except Exception as e:
        print(f"[ToolExecutions] Failed to log {tool_name}: {e}")
