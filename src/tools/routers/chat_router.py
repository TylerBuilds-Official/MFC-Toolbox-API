from src.tools.state.state_handler import StateHandler
from src.tools.state.settings_manager import SettingsManager


class ChatRouter:
    def __init__(self, settings_manager: SettingsManager, state_handler: StateHandler, openai_handler, anthropic_handler):
        self.settings_manager = settings_manager
        self.state_handler = state_handler
        self.handlers = {"openai": openai_handler, "anthropic": anthropic_handler}


    def handle_message(self, user_message: str, model: str=None, provider: str=None) -> str:
        if provider is None:
            if model is not None:
                provider = self._infer_provider_from_model(model)
            else:
                provider = self.settings_manager.get_provider()

        if model is None:
            model = self.settings_manager.get_default_model()

        handler = self.handlers.get(provider)
        if not handler:
            raise ValueError(f"Invalid provider: {provider}")

        return handler.handle_message(user_message, model=model)


    def _infer_provider_from_model(self, model: str) -> str:
        """
        Infer the provider from the model name.
        Claude models start with 'claude', OpenAI models start with 'gpt'.
        """
        if model.startswith("claude"):
            return "anthropic"
        elif model.startswith("gpt"):
            return "openai"
        else:
            return self.settings_manager.get_provider()

