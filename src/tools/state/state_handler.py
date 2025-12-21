import uuid


class StateHandler:
    """
    Manages conversation state for MVP single-user, single-session usage.
    
    Note: State is held in memory only. Restarting the server or calling
    reset() will clear all conversation context.
    """
    
    def __init__(self):
        self.conversation_id = None
        self.state = {}
        self._initialize_state()

    def _initialize_state(self):
        """Set up fresh default state with a new conversation ID."""
        self.conversation_id = str(uuid.uuid4())
        self.state = {
            "conversation_id":      self.conversation_id,
            "is_developer":         False,
            "save_memories":        False,
            "conversation_summary": "",
            "turn_count":           0
        }

    def reset(self):
        """Reset all state for a fresh conversation."""
        self._initialize_state()

    def set_conversation_id(self, conversation_id: str = None):
        """Set or generate a conversation ID and sync to state."""
        if conversation_id:
            self.conversation_id = conversation_id
        elif not self.conversation_id:
            self.conversation_id = str(uuid.uuid4())
        
        # Keep state dict in sync
        self.state["conversation_id"] = self.conversation_id

    def get_conversation_id(self) -> str:
        if self.conversation_id is None:
            self.set_conversation_id()
        return self.conversation_id

    def update_state(self, updates: dict):
        """Merge updates into current state."""
        self.state.update(updates)

    def get_state(self) -> dict:
        return self.state

    def update_state_from_message(self, message: str):
        """Parse message for special keywords/triggers that modify state."""
        if "keyword: snowy" in message.lower():
            self.state["is_developer"] = True

    def append_to_summary(self, user_message: str, assistant_reply: str, max_chars: int = 120):
        """
        Append a turn to the conversation summary.
        
        Truncates messages to max_chars to keep the summary compact
        while preserving context for the model.
        """
        user_truncated = user_message[:max_chars]
        assistant_truncated = assistant_reply[:max_chars]
        
        self.state["conversation_summary"] += (
            f"- User: {user_truncated}\n"
            f"- Assistant: {assistant_truncated}\n"
        )

    def increment_turn(self):
        """Increment the turn counter."""
        self.state["turn_count"] += 1

    def get_turn_count(self) -> int:
        return self.state["turn_count"]
