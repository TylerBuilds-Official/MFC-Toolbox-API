from src.tools.sql_tools.memories import (
    get_user_memories,
    search_memories,
    get_memory,
    create_memory,
    update_memory,
    delete_memory,
)
from src.utils.memory_utils.memory import Memory


class MemoryService:
    """Handles user memory CRUD operations."""

    VALID_MEMORY_TYPES = {"fact", "preference", "project", "skill", "context"}
    DEFAULT_MEMORY_TYPE = "fact"

    @staticmethod
    def _row_to_memory(data: dict) -> Memory:
        """Convert a database row dict to a Memory object."""
        return Memory(
            id=data.get("Id"),
            user_id=data.get("UserId"),
            memory_type=data.get("MemoryType"),
            content=data.get("Content"),
            source_conversation_id=data.get("SourceConversationId"),
            source_message_id=data.get("SourceMessageId"),
            created_at=data.get("CreatedAt"),
            updated_at=data.get("UpdatedAt"),
            is_active=data.get("IsActive"),
        )

    @staticmethod
    def get_memories(user_id: int, limit: int = 15) -> list[Memory]:
        """
        Get active memories for a user, ordered by most recent.
        Used for system prompt injection.
        
        Args:
            user_id: The user's ID
            limit: Maximum memories to return (default 15)
            
        Returns:
            List of Memory objects
        """
        rows = get_user_memories(user_id, limit)
        return [MemoryService._row_to_memory(row) for row in rows]

    @staticmethod
    def search(user_id: int, query: str, limit: int = 10) -> list[Memory]:
        """
        Search user's memories by keyword.
        Used by MCP tool for history search.
        
        Args:
            user_id: The user's ID
            query: Search keywords
            limit: Maximum results
            
        Returns:
            List of matching Memory objects
        """
        rows = search_memories(user_id, query, limit)
        return [MemoryService._row_to_memory(row) for row in rows]

    @staticmethod
    def get_memory(memory_id: int, user_id: int) -> Memory | None:
        """
        Get a single memory by ID.
        
        Args:
            memory_id: The memory's ID
            user_id: The user's ID (ownership check)
            
        Returns:
            Memory object or None
        """
        data = get_memory(memory_id, user_id)
        if data is None:
            return None
        return MemoryService._row_to_memory(data)

    @staticmethod
    def create_memory(
        user_id: int,
        content: str,
        memory_type: str = "fact",
        source_conversation_id: int = None,
        source_message_id: int = None
    ) -> Memory:
        """
        Create a new memory.
        
        Args:
            user_id: The user's ID
            content: Memory content
            memory_type: Type ('fact', 'preference', 'project', 'skill', 'context')
            source_conversation_id: Optional source conversation
            source_message_id: Optional source message
            
        Returns:
            Created Memory object
            
        Raises:
            ValueError: If memory_type is invalid
        """
        if memory_type not in MemoryService.VALID_MEMORY_TYPES:
            raise ValueError(
                f"Invalid memory_type '{memory_type}'. "
                f"Must be one of: {MemoryService.VALID_MEMORY_TYPES}"
            )
        
        data = create_memory(
            user_id=user_id,
            content=content,
            memory_type=memory_type,
            source_conversation_id=source_conversation_id,
            source_message_id=source_message_id,
        )
        return MemoryService._row_to_memory(data)

    @staticmethod
    def update_memory(memory_id: int, user_id: int, updates: dict) -> Memory | None:
        """
        Update a memory's content or type.
        
        Args:
            memory_id: The memory's ID
            user_id: The user's ID (ownership check)
            updates: Dict with 'content' and/or 'memory_type'
            
        Returns:
            Updated Memory object or None if not found
            
        Raises:
            ValueError: If memory_type is invalid
        """
        if "memory_type" in updates:
            if updates["memory_type"] not in MemoryService.VALID_MEMORY_TYPES:
                raise ValueError(
                    f"Invalid memory_type '{updates['memory_type']}'. "
                    f"Must be one of: {MemoryService.VALID_MEMORY_TYPES}"
                )
        
        success = update_memory(memory_id, user_id, updates)
        if not success:
            return None
        
        return MemoryService.get_memory(memory_id, user_id)

    @staticmethod
    def delete_memory(memory_id: int, user_id: int) -> bool:
        """
        Soft delete a memory.
        
        Args:
            memory_id: The memory's ID
            user_id: The user's ID (ownership check)
            
        Returns:
            True if deleted, False if not found
        """
        return delete_memory(memory_id, user_id)

    @staticmethod
    def format_for_prompt(memories: list[Memory]) -> str:
        """
        Format memories for system prompt injection.
        
        Args:
            memories: List of Memory objects
            
        Returns:
            Formatted string for system prompt
        """
        if not memories:
            return ""
        
        lines = ["## User Memories", ""]
        
        # Group by type for cleaner presentation
        by_type = {}
        for mem in memories:
            if mem.memory_type not in by_type:
                by_type[mem.memory_type] = []
            by_type[mem.memory_type].append(mem.content)
        
        # Order: project, skill, fact, preference, context
        type_order = ["project", "skill", "fact", "preference", "context"]
        
        for mem_type in type_order:
            if mem_type in by_type:
                lines.append(f"**{mem_type.capitalize()}s:**")
                for content in by_type[mem_type]:
                    lines.append(f"- {content}")
                lines.append("")
        
        return "\n".join(lines)
