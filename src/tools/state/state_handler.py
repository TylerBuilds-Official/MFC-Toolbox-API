class StateHandler:
    """
    Manages conversation state for a single conversation.
    
    Can be initialized fresh or loaded from persisted state.
    State should be saved after each turn via to_dict().
    """
    
    DEFAULT_STATE = {
        "is_developer": False,
        "save_memories": False,
        "conversation_summary": "",
        "turn_count": 0
    }
    
    def __init__(self, conversation_id: int = None):
        self.conversation_id = conversation_id
        self.state = dict(self.DEFAULT_STATE)
    
    @classmethod
    def from_dict(cls, conversation_id: int, state: dict) -> "StateHandler":
        """
        Create a StateHandler from persisted state.
        
        Args:
            conversation_id: The conversation's ID
            state: Previously saved state dict
            
        Returns:
            StateHandler initialized with the provided state
        """
        handler = cls(conversation_id)
        
        # Merge saved state with defaults (in case new fields were added)
        for key in cls.DEFAULT_STATE:
            if key in state:
                handler.state[key] = state[key]
        
        return handler
    
    def to_dict(self) -> dict:
        """
        Serialize state for persistence.
        
        Returns:
            State dict ready for JSON serialization
        """
        return dict(self.state)
    
    def reset(self):
        """Reset to fresh default state."""
        self.state = dict(self.DEFAULT_STATE)

    def update_state(self, updates: dict):
        """Update state with provided values."""
        self.state.update(updates)

    def get_state(self) -> dict:
        """Get current state dict."""
        return self.state

    def update_state_from_message(self, message: str):
        """Parse message for special keywords/triggers that modify state."""
        if "keyword: snowy" in message.lower():
            self.state["is_developer"] = True

    def append_to_summary(self, user_message: str, assistant_reply: str, max_chars: int = 400):
        """
        Append a turn to the conversation summary.
        
        Args:
            user_message: The user's message
            assistant_reply: The assistant's response
            max_chars: Max characters to keep from each message, default is 400
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
        """Get current turn count."""
        return self.state["turn_count"]
    
    def get_summary(self) -> str:
        """Get the conversation summary."""
        return self.state.get("conversation_summary", "")
