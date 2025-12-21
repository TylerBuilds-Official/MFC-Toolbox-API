# src/tools/state/settings_manager.py


class SettingsManager:
    """
    Manages user settings and preferences.

    MVP: In-memory storage (resets on server restart)
    Future: Load/save from SQL database per user
    """

    def __init__(self):
        self.settings = self._get_default_settings()

    def _get_default_settings(self) -> dict:
        """Default settings for new users"""
        return {
            "provider": "openai",
            "default_model": "gpt-4o",
            "openai_api_key": None,
            "anthropic_api_key": None,
            "auto_save_conversations": True,
            "dark_mode": True,
        }

    def get_provider(self) -> str:
        return self.settings.get("provider", "openai")

    def set_provider(self, provider: str):
        if provider not in ["openai", "anthropic"]:
            raise ValueError(f"Invalid provider: {provider}")

        self.settings["provider"] = provider

        if provider == "openai" and self.settings["default_model"].startswith("claude"):
            self.settings["default_model"] = "gpt-4o"
        elif provider == "anthropic" and self.settings["default_model"].startswith("gpt"):
            self.settings["default_model"] = "claude-sonnet-4-5-20250929"

    def get_default_model(self) -> str:
        """Get the current default model (no validation needed - just return it)"""
        return self.settings.get("default_model")

    def set_default_model(self, model: str):
        """Set default model with validation"""
        from src.data.valid_models import VALID_OA_MODELS, VALID_ANT_MODELS

        provider = self.get_provider()
        valid_models = VALID_OA_MODELS if provider == "openai" else VALID_ANT_MODELS

        if model not in valid_models:
            raise ValueError(f"Invalid model '{model}' for provider '{provider}'. Must be one of {valid_models}")

        self.settings["default_model"] = model

    def get_all_settings(self) -> dict:
        return self.settings.copy()

    def update_settings(self, updates: dict):
        """Bulk update settings"""
        self.settings.update(updates)

    def reset(self):
        """Reset to defaults"""
        self.settings = self._get_default_settings()