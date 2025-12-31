from src.tools.sql_tools.get_user_settings import get_user_settings
from src.tools.sql_tools.update_current_model import update_current_model
from src.tools.sql_tools.update_provider import update_model_provider
from src.tools.sql_tools.mssql_pool import get_mssql_connection, SCHEMA
from src.utils.settings_utils.user_settings import UserSettings


class UserSettingsService:
    """Handles user settings CRUD operations against MS SQL."""

    VALID_PROVIDERS = {"openai", "anthropic"}
    DEFAULT_PROVIDER = "openai"
    DEFAULT_MODEL = "gpt-4o"
    VALID_REASONING_EFFORTS = {"low", "medium", "high"}

    @staticmethod
    def get_settings(user_id: int) -> UserSettings:
        """
        Fetch user's settings from DB.
        Returns defaults if not found (shouldn't happen due to trigger).
        """
        settings = get_user_settings(user_id, UserSettingsService)

        return UserSettings(
            user_id=settings.get("user_id"),
            provider=settings.get("provider") or UserSettingsService.DEFAULT_PROVIDER,
            default_model=settings.get("default_model") or UserSettingsService.DEFAULT_MODEL,
            enable_streaming=settings.get("enable_streaming", True),
            enable_extended_thinking=settings.get("enable_extended_thinking", False),
            openai_reasoning_effort=settings.get("openai_reasoning_effort", "medium"),
            anthropic_thinking_budget=settings.get("anthropic_thinking_budget", 10000),
            memory_limit=settings.get("memory_limit", 15),
            updated_at=settings.get("updated_at")
        )

    @staticmethod
    def update_provider(user_id: int, provider: str, default_model: str = None) -> UserSettings:
        """
        Update user's provider and optionally the default model.
        Auto-switches model if current model is incompatible with new provider.
        """
        data = update_model_provider(user_id, provider, default_model, user_settings_service=UserSettingsService)

        # Re-fetch full settings to get all fields
        return UserSettingsService.get_settings(user_id)

    @staticmethod
    def update_model(user_id: int, model: str) -> UserSettings:
        """
        Update user's default model.
        Validates model is compatible with current provider.
        """
        data = update_current_model(user_id, model, user_settings_service=UserSettingsService)

        # Re-fetch full settings to get all fields
        return UserSettingsService.get_settings(user_id)

    @staticmethod
    def update_streaming_settings(
        user_id: int,
        enable_streaming: bool = None,
        enable_extended_thinking: bool = None,
        openai_reasoning_effort: str = None,
        anthropic_thinking_budget: int = None,
        memory_limit: int = None
    ) -> UserSettings:
        """
        Update streaming, thinking, and memory settings.
        Only updates fields that are explicitly provided.
        """
        # Validate inputs
        if openai_reasoning_effort and openai_reasoning_effort not in UserSettingsService.VALID_REASONING_EFFORTS:
            raise ValueError(f"Invalid reasoning effort: {openai_reasoning_effort}. Must be one of {UserSettingsService.VALID_REASONING_EFFORTS}")
        
        if anthropic_thinking_budget and (anthropic_thinking_budget < 1000 or anthropic_thinking_budget > 100000):
            raise ValueError("Thinking budget must be between 1000 and 100000")
        
        if memory_limit is not None and (memory_limit < 0 or memory_limit > 50):
            raise ValueError("Memory limit must be between 0 and 50")

        # Build SET clause dynamically
        updates = []
        params = []
        
        if enable_streaming is not None:
            updates.append("EnableStreaming = ?")
            params.append(1 if enable_streaming else 0)
        
        if enable_extended_thinking is not None:
            updates.append("EnableExtendedThinking = ?")
            params.append(1 if enable_extended_thinking else 0)
        
        if openai_reasoning_effort is not None:
            updates.append("OpenAIReasoningEffort = ?")
            params.append(openai_reasoning_effort)
        
        if anthropic_thinking_budget is not None:
            updates.append("AnthropicThinkingBudget = ?")
            params.append(anthropic_thinking_budget)
        
        if memory_limit is not None:
            updates.append("MemoryLimit = ?")
            params.append(memory_limit)
        
        if not updates:
            return UserSettingsService.get_settings(user_id)
        
        updates.append("UpdatedAt = GETDATE()")
        params.append(user_id)
        
        with get_mssql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE {SCHEMA}.UserSettings SET {', '.join(updates)} WHERE UserId = ?",
                params
            )
            conn.commit()
            cursor.close()
        
        return UserSettingsService.get_settings(user_id)

    @staticmethod
    def update_settings(user_id: int, updates: dict) -> UserSettings:
        """
        Bulk update settings.
        Handles all setting types: provider, model, streaming, and thinking.
        """
        current = UserSettingsService.get_settings(user_id)

        # Handle provider/model changes first
        new_provider = updates.get("provider", current.provider)
        new_model = updates.get("default_model", current.default_model)

        if new_provider != current.provider:
            UserSettingsService.update_provider(user_id, new_provider, new_model)
        elif new_model != current.default_model:
            UserSettingsService.update_model(user_id, new_model)

        # Handle streaming/thinking/memory settings
        other_updates = {}
        if "enable_streaming" in updates:
            other_updates["enable_streaming"] = updates["enable_streaming"]
        if "enable_extended_thinking" in updates:
            other_updates["enable_extended_thinking"] = updates["enable_extended_thinking"]
        if "openai_reasoning_effort" in updates:
            other_updates["openai_reasoning_effort"] = updates["openai_reasoning_effort"]
        if "anthropic_thinking_budget" in updates:
            other_updates["anthropic_thinking_budget"] = updates["anthropic_thinking_budget"]
        if "memory_limit" in updates:
            other_updates["memory_limit"] = updates["memory_limit"]

        if other_updates:
            return UserSettingsService.update_streaming_settings(user_id, **other_updates)

        return UserSettingsService.get_settings(user_id)
