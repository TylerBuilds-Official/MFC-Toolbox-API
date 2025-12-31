from src.utils.memory_utils import MemoryService


def oa_save_user_memory(
    content: str, 
    memory_type: str = "fact",
    user_id: int = None,
    conversation_id: int = None
):
    """
    Save a new memory about the user.
    
    Use this when you learn something important about the user that should
    be remembered for future conversations, such as:
    - Personal facts (name, role, preferences)
    - Projects they're working on
    - Skills or expertise
    - Preferences for how they like to work
    
    Args:
        content: The memory content to save
        memory_type: Type of memory - 'fact', 'preference', 'project', 'skill', 'context'
        user_id: Injected server-side, not provided by LLM
        conversation_id: Injected server-side, not provided by LLM
        
    Returns:
        The created memory
    """
    if user_id is None:
        return {"error": "User context not available"}
    
    # Validate memory_type
    valid_types = {"fact", "preference", "project", "skill", "context"}
    if memory_type not in valid_types:
        return {"error": f"Invalid memory_type '{memory_type}'. Must be one of: {valid_types}"}
    
    try:
        memory = MemoryService.create_memory(
            user_id=user_id,
            content=content,
            memory_type=memory_type,
            source_conversation_id=conversation_id
        )
        return {
            "success": True,
            "memory": {
                "id": memory.id,
                "type": memory.memory_type,
                "content": memory.content
            }
        }
    except Exception as e:
        return {"error": str(e)}


__all__ = ['oa_save_user_memory']
