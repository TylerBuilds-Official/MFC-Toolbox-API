from src.tools.sql_tools import get_conversation_messages


def oa_get_conversation_messages(conversation_id: int, user_id: int = None):
    """
    Fetch full message history for a specific conversation.
    
    Args:
        conversation_id: The conversation ID to retrieve
        user_id: Injected server-side, not provided by LLM
        
    Returns:
        Dict with conversation metadata and all messages
    """
    if user_id is None:
        return {"error": "User context not available"}
    
    if not conversation_id:
        return {"error": "Conversation ID is required"}
    
    try:
        result = get_conversation_messages(conversation_id, user_id)
        if result is None:
            return {"error": "Conversation not found or access denied"}
        return result
    except Exception as e:
        return {"error": str(e)}


__all__ = ['oa_get_conversation_messages']
