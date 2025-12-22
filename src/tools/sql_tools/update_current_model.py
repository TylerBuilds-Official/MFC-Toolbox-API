from datetime import datetime
from src.tools.sql_tools.mssql_pool import get_mssql_connection, SCHEMA
from src.data.valid_models import VALID_OA_MODELS, VALID_ANT_MODELS


def update_current_model(user_id: int, model: str, user_settings_service=None):
    if user_settings_service is None:
        from src.utils.settings_utils.user_settings_service import UserSettingsService
        user_settings_service = UserSettingsService

    current = user_settings_service.get_settings(user_id)
    valid_models = VALID_OA_MODELS if current.provider == "openai" else VALID_ANT_MODELS

    if model not in valid_models:
        raise ValueError(f"Invalid model '{model}' for provider '{current.provider}'. Must be one of {valid_models}")

    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE {SCHEMA}.UserSettings "
            f"SET DefaultModel = ?, UpdatedAt = GETDATE() "
            f"WHERE UserId = ?",
            (model, user_id)
        )
        cursor.close()

    data = {
        "user_id": user_id,
        "provider": current.provider,
        "default_model": model,
        "updated_at": datetime.now()
    }

    return data
