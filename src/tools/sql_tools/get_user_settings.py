from src.tools.sql_tools.mssql_pool import get_mssql_connection, SCHEMA

def get_user_settings(user_id: int, user_settings_service):
    """
    Fetch user settings from database.
    Returns all settings including streaming/thinking preferences.
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""SELECT 
                UserId, 
                Provider, 
                DefaultModel, 
                EnableStreaming,
                EnableExtendedThinking,
                OpenAIReasoningEffort,
                AnthropicThinkingBudget,
                UpdatedAt 
            FROM {SCHEMA}.UserSettings 
            WHERE UserId = ?""",
            (user_id,)
        )
        row = cursor.fetchone()
        cursor.close()

        if row:
            return {
                "user_id": row[0],
                "provider": row[1] or user_settings_service.DEFAULT_PROVIDER,
                "default_model": row[2] or user_settings_service.DEFAULT_MODEL,
                "enable_streaming": bool(row[3]) if row[3] is not None else True,
                "enable_extended_thinking": bool(row[4]) if row[4] is not None else False,
                "openai_reasoning_effort": row[5] or "medium",
                "anthropic_thinking_budget": row[6] or 10000,
                "updated_at": row[7]
            }

        # Fallback if no settings found (shouldn't happen due to trigger)
        return {
            "user_id": user_id,
            "provider": user_settings_service.DEFAULT_PROVIDER,
            "default_model": user_settings_service.DEFAULT_MODEL,
            "enable_streaming": True,
            "enable_extended_thinking": False,
            "openai_reasoning_effort": "medium",
            "anthropic_thinking_budget": 10000,
            "updated_at": None
        }
