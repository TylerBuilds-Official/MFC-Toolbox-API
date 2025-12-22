from src.tools.sql_tools.get_user_settings import get_user_settings
from src.tools.sql_tools.update_current_model import update_current_model
from src.tools.sql_tools.update_provider import update_model_provider
from src.utils.settings_utils.user_settings import UserSettings


class UserSettingsService:
    """Handles user settings CRUD operations against MS SQL."""


    VALID_PROVIDERS = {"openai", "anthropic"}
    DEFAULT_PROVIDER = "openai"
    DEFAULT_MODEL = "gpt-4o"




    @staticmethod
    def get_settings(user_id: int) -> UserSettings:
        """
        Fetch user's settings from DB.
        Returns defaults if not found (shouldn't happen due to trigger).
        """
        # Fallback to defaults if not found in DB in get_user_settings
        settings = get_user_settings(user_id, UserSettingsService)

        return UserSettings(
            user_id=settings.get("user_id"),
            provider=settings.get("provider") or UserSettingsService.DEFAULT_PROVIDER,
            default_model=settings.get("default_model") or UserSettingsService.DEFAULT_MODEL,
            updated_at=settings.get("updated_at")
        )




    @staticmethod
    def update_provider(user_id: int, provider: str, default_model: str = None) -> UserSettings:
        """
        Update user's provider and optionally the default model.
        Auto-switches model if current model is incompatible with new provider.

        Args:
            user_id: User's internal ID
            provider: New provider ('openai' or 'anthropic')
            default_model: Optional new default model

        Returns:
            Updated UserSettings

        Raises:
            ValueError: If provider is invalid
        """
        data = update_model_provider(user_id, provider, default_model, user_settings_service=UserSettingsService)

        return UserSettings(
            user_id=data["user_id"],
            provider=data["provider"],
            default_model=data["default_model"],
            updated_at=data["updated_at"]
        )



    @staticmethod
    def update_model(user_id: int, model: str) -> UserSettings:
        """
        Update user's default model.
        Validates model is compatible with current provider.

        Args:
            user_id: User's internal ID
            model: New default model

        Returns:
            Updated UserSettings

        Raises:
            ValueError: If model is invalid for current provider
        """
        data = update_current_model(user_id, model, user_settings_service=UserSettingsService)

        return UserSettings(
            user_id=data["user_id"],
            provider=data["provider"],
            default_model=data["default_model"],
            updated_at=data["updated_at"]
        )



    @staticmethod
    def update_settings(user_id: int, updates: dict) -> UserSettings:
        """
        Bulk update settings. Currently only processes provider and default_model.
        Other fields (auto_save_conversations, dark_mode) are ignored until DB columns exist.

        Args:
            user_id: User's internal ID
            updates: Dict of settings to update

        Returns:
            Updated UserSettings
        """
        current = UserSettingsService.get_settings(user_id)

        new_provider = updates.get("provider", current.provider)
        new_model = updates.get("default_model", current.default_model)

        if new_provider != current.provider:
            return UserSettingsService.update_provider(user_id, new_provider, new_model)

        if new_model != current.default_model:
            return UserSettingsService.update_model(user_id, new_model)

        # Nothing changed
        return current
