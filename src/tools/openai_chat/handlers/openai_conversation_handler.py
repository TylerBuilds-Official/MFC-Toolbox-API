from src.data.instructions import Instructions
from src.tools.state.state_handler import StateHandler
from src.tools.openai_chat.handlers.openai_message_handler import OpenAIMessageHandler
from src.tools.auth import User


class OpenAIConversationHandler:
    def __init__(self, state_handler: StateHandler, message_handler: OpenAIMessageHandler):
        self.state_handler = state_handler
        self.message_handler = message_handler

    def handle_message(self, user_message: str, model: str = "gpt-4o", user: User = None, memories_text: str = None, conversation_id: int = None) -> str:
        """
        Process a single conversation turn.
        
        1. Update state based on message content
        2. Build dynamic instructions from current state
        3. Get assistant response from OpenAI
        4. Update conversation summary
        5. Return the assistant's reply
        """
        # Update state flags based on message content (e.g., developer mode)
        self.state_handler.update_state_from_message(user_message)
        
        # Get current state and build instructions
        state = self.state_handler.get_state()
        state["conversation_id"] = conversation_id  # Add for recent exchanges lookup
        instructions = Instructions(state, user=user, memories_text=memories_text).build_instructions()
        
        # Build tool context for user-aware tools
        tool_context = None
        if user:
            tool_context = {
                "user_id": user.id,
                "conversation_id": conversation_id
            }
        
        # Get response from OpenAI
        assistant_reply = self.message_handler.handle_message(
            instructions=instructions,
            message=user_message,
            model=model,
            tool_context=tool_context
        )
        
        # Update conversation summary for context in future turns
        self.state_handler.append_to_summary(
            user_message=user_message,
            assistant_reply=assistant_reply
        )
        
        # Increment turn count
        self.state_handler.increment_turn()
        
        return assistant_reply
