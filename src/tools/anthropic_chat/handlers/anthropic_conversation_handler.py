from src.data.instructions import Instructions
from src.tools.state.state_handler import StateHandler
from src.tools.anthropic_chat.handlers.anthropic_message_handler import AnthropicMessageHandler

class AnthropicConversationHandler:
    def __init__(self, state_handler: StateHandler, message_handler: AnthropicMessageHandler):
        self.state_handler = state_handler
        self.message_handler = message_handler

    def handle_message(self, user_message: str, model: str="claude-sonnet-4-5-20250929") -> str:
        self.state_handler.update_state_from_message(user_message)
        state = self.state_handler.get_state()
        instructions = Instructions(state).build_instructions()

        assistant_reply = self.message_handler.handle_message(instructions=instructions,
                                                              message=user_message,
                                                              model=model)

        self.state_handler.append_to_summary(user_message=user_message,
                                             assistant_reply=assistant_reply)
        self.state_handler.increment_turn()

        return assistant_reply