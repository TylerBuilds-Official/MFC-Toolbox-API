from src.tools.sql_tools.mssql_pool import get_mssql_connection, SCHEMA

def get_user_settings(user_id: int, user_settings_service):
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT UserId, Provider, DefaultModel, UpdatedAt "
            f"FROM {SCHEMA}.UserSettings WHERE UserId = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        cursor.close()

        if row:
            data = {
                "user_id": row[0],
                "provider": row[1] or user_settings_service.DEFAULT_PROVIDER,
                "default_model": row[2] or user_settings_service.DEFAULT_MODEL,
                "updated_at": row[3]
            }

            return data

        # Fallback if no settings found
        return {
            "user_id": user_id,
            "provider": user_settings_service.DEFAULT_PROVIDER,
            "default_model": user_settings_service.DEFAULT_MODEL,
            "updated_at": None
        }

