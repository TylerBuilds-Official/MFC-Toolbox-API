from datetime import datetime

from src.data.valid_models import VALID_OA_MODELS, VALID_ANT_MODELS
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def update_model_provider(user_id: int, provider: str, default_model: str = None, user_settings_service=None):
    if user_settings_service is None:
        from src.utils.settings_utils.user_settings_service import UserSettingsService
        user_settings_service = UserSettingsService

    if provider not in user_settings_service.VALID_PROVIDERS:
        raise ValueError(f"Invalid provider '{provider}'. Must be one of: {user_settings_service.VALID_PROVIDERS}")

    # Get current settings to check model compatibility
    current = user_settings_service.get_settings(user_id)

    # Determine new model
    if default_model:
        new_model = default_model
    elif provider != current.provider:
        # Provider changed - check if current model is compatible
        if provider == "openai" and current.default_model.startswith("claude"):
            new_model = "gpt-4o"
        elif provider == "anthropic" and current.default_model.startswith("gpt"):
            new_model = "claude-sonnet-4-5-20250929"
        else:
            new_model = current.default_model
    else:
        new_model = current.default_model

    valid_models = VALID_OA_MODELS if provider == "openai" else VALID_ANT_MODELS
    if new_model not in valid_models:
        raise ValueError(f"Invalid model '{new_model}' for provider '{provider}'. Must be one of {valid_models}")

    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE {SCHEMA}.UserSettings "
            f"SET Provider = ?, DefaultModel = ?, UpdatedAt = GETDATE() "
            f"WHERE UserId = ?",
            (provider, new_model, user_id)
        )
        cursor.close()

    data = {
        "user_id": user_id,
        "provider": provider,
        "default_model": new_model,
        "updated_at": datetime.now()
    }

    return data
