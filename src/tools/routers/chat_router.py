from src.tools.state.state_handler import StateHandler


class ChatRouter:
    """
    Routes chat messages to the appropriate provider handler.
    Provider and model must be specified explicitly (resolved at endpoint level).
    """

    def __init__(self, settings_manager, state_handler: StateHandler, openai_handler, anthropic_handler):
        # settings_manager kept for signature compatibility but no longer used
        self.state_handler = state_handler
        self.handlers = {"openai": openai_handler, "anthropic": anthropic_handler}

    def handle_message(self, user_message: str, model: str, provider: str) -> str:
        """
        Route message to the appropriate provider handler.

        Args:
            user_message: The user's message
            model: Model to use (required)
            provider: Provider to use (required)

        Returns:
            Assistant's response

        Raises:
            ValueError: If provider is invalid or model/provider not specified
        """
        if not provider:
            raise ValueError("Provider must be specified")
        if not model:
            raise ValueError("Model must be specified")

        handler = self.handlers.get(provider)
        if not handler:
            raise ValueError(f"Invalid provider: {provider}. Must be 'openai' or 'anthropic'")

        return handler.handle_message(user_message, model=model)

    @staticmethod
    def infer_provider_from_model(model: str) -> str:
        """
        Infer the provider from the model name.
        Claude models start with 'claude', OpenAI models start with 'gpt'.

        Returns None if cannot be inferred.
        """
        if model.startswith("claude"):
            return "anthropic"
        elif model.startswith("gpt"):
            return "openai"
        return None