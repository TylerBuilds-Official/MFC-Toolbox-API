from src.utils.memory_utils import MemoryService


def oa_delete_user_memory(
    memory_id: int,
    user_id: int = None
):
    """
    Delete (soft-delete) a memory that is no longer relevant.
    
    Use when:
    - Information is outdated (user changed jobs, finished a project, etc.)
    - Memory was saved incorrectly
    - User explicitly asks to forget something
    
    Args:
        memory_id: The ID of the memory to delete
        user_id: Injected server-side, not provided by LLM
        
    Returns:
        Success or error message
    """
    if user_id is None:
        return {"error": "User context not available"}
    
    try:
        success = MemoryService.delete_memory(memory_id, user_id)
        if not success:
            return {"error": f"Memory {memory_id} not found or access denied"}
        
        return {
            "success": True,
            "message": f"Memory {memory_id} deleted"
        }
    except Exception as e:
        return {"error": str(e)}


__all__ = ['oa_delete_user_memory']
