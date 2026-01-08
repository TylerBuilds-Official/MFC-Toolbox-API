from src.utils.memory_utils import MemoryService


def oa_update_user_memory(
    memory_id: int,
    content: str = None,
    memory_type: str = None,
    user_id: int = None
):
    """
    Update an existing memory's content or type.
    
    Args:
        memory_id: The ID of the memory to update
        content: New content (optional)
        memory_type: New type (optional)
        user_id: Injected server-side, not provided by LLM
        
    Returns:
        The updated memory or error
    """
    if user_id is None:
        return {"error": "User context not available"}
    
    if content is None and memory_type is None:
        return {"error": "Must provide content or memory_type to update"}
    
    # Validate memory_type if provided
    valid_types = {"fact", "preference", "project", "skill", "context"}
    if memory_type is not None and memory_type not in valid_types:
        return {"error": f"Invalid memory_type '{memory_type}'. Must be one of: {valid_types}"}
    
    updates = {}
    if content is not None:
        updates["content"] = content
    if memory_type is not None:
        updates["memory_type"] = memory_type
    
    try:
        memory = MemoryService.update_memory(memory_id, user_id, updates)
        if memory is None:
            return {"error": f"Memory {memory_id} not found or access denied"}
        
        return {
            "success": True,
            "memory": {
                "id": memory.id,
                "type": memory.memory_type,
                "content": memory.content,
                "reference_count": memory.reference_count
            }
        }
    except Exception as e:
        return {"error": str(e)}


__all__ = ['oa_update_user_memory']
