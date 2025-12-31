import json
from src.tools.sql_tools.conversation_state import get_conversation_state, upsert_conversation_state


class ConversationStateService:
    """
    Handles conversation state persistence.
    
    Wraps SQL operations and handles JSON serialization/deserialization.
    """

    @staticmethod
    def get_state(conversation_id: int) -> dict | None:
        """
        Load state for a conversation from the database.
        
        Args:
            conversation_id: The conversation's ID
            
        Returns:
            Deserialized state dict or None if not found
        """
        row = get_conversation_state(conversation_id)
        
        if row is None:
            return None
        
        try:
            state = json.loads(row["state_json"]) if row["state_json"] else {}
            # Ensure turn_count from DB is in sync
            state["turn_count"] = row["turn_count"]
            return state
        except json.JSONDecodeError:
            # Corrupted state, return None to trigger fresh start
            return None

    @staticmethod
    def save_state(conversation_id: int, state: dict) -> bool:
        """
        Persist state for a conversation to the database.
        
        Args:
            conversation_id: The conversation's ID
            state: State dict to persist
            
        Returns:
            True if successful
        """
        state_json = json.dumps(state, default=str)
        turn_count = state.get("turn_count", 0)
        
        return upsert_conversation_state(conversation_id, state_json, turn_count)
