from src.tools.sql_tools.memories import (
    get_user_memories,
    get_all_memories,
    get_stale_memories,
    search_memories,
    get_memory,
    create_memory,
    update_memory,
    refresh_memory,
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
            last_referenced_at=data.get("LastReferencedAt"),
            reference_count=data.get("ReferenceCount", 0),
            expires_at=data.get("ExpiresAt"),
        )

    # =========================================================================
    # Core CRUD
    # =========================================================================

    @staticmethod
    def get_memories(user_id: int, limit: int = 15) -> list[Memory]:
        """
        Get active memories for a user, ordered by most recent.
        Used for system prompt injection. Does NOT track reference.
        
        Args:
            user_id: The user's ID
            limit: Maximum memories to return (default 15)
            
        Returns:
            List of Memory objects
        """
        rows = get_user_memories(user_id, limit)
        return [MemoryService._row_to_memory(row) for row in rows]

    @staticmethod
    def get_all_memories(
        user_id: int, 
        memory_type: str = None,
        include_inactive: bool = False,
        include_expired: bool = False
    ) -> list[Memory]:
        """
        Get all memories for a user with optional filters.
        Used for UI memory management.
        
        Args:
            user_id: The user's ID
            memory_type: Filter by type (optional)
            include_inactive: Include soft-deleted memories
            include_expired: Include expired memories
            
        Returns:
            List of Memory objects
        """
        rows = get_all_memories(user_id, memory_type, include_inactive, include_expired)
        return [MemoryService._row_to_memory(row) for row in rows]

    @staticmethod
    def search(user_id: int, query: str, limit: int = 10, track_reference: bool = True) -> list[Memory]:
        """
        Search user's memories by keyword.
        Updates LastReferencedAt and ReferenceCount for results.
        
        Args:
            user_id: The user's ID
            query: Search keywords
            limit: Maximum results
            track_reference: Update reference tracking (default True)
            
        Returns:
            List of matching Memory objects
        """
        rows = search_memories(user_id, query, limit, track_reference)
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
        source_message_id: int = None,
        expires_at: str = None
    ) -> Memory:
        """
        Create a new memory.
        
        Args:
            user_id: The user's ID
            content: Memory content
            memory_type: Type ('fact', 'preference', 'project', 'skill', 'context')
            source_conversation_id: Optional source conversation
            source_message_id: Optional source message
            expires_at: Optional expiration datetime (ISO format)
            
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
            expires_at=expires_at,
        )
        return MemoryService._row_to_memory(data)

    @staticmethod
    def update_memory(memory_id: int, user_id: int, updates: dict) -> Memory | None:
        """
        Update a memory's content, type, or expiration.
        
        Args:
            memory_id: The memory's ID
            user_id: The user's ID (ownership check)
            updates: Dict with 'content', 'memory_type', and/or 'expires_at'
            
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

    # =========================================================================
    # Staleness & Lifecycle
    # =========================================================================

    @staticmethod
    def get_stale_memories(user_id: int, days: int = 90) -> list[Memory]:
        """
        Get memories that haven't been referenced in X days.
        Used for stale memory review in UI.
        
        Args:
            user_id: The user's ID
            days: Days without reference to consider stale (default 90)
            
        Returns:
            List of stale Memory objects
        """
        rows = get_stale_memories(user_id, days)
        return [MemoryService._row_to_memory(row) for row in rows]

    @staticmethod
    def refresh_memory(memory_id: int, user_id: int) -> bool:
        """
        Refresh a memory's staleness by updating LastReferencedAt.
        Used when user explicitly confirms a memory is still relevant.
        
        Args:
            memory_id: The memory's ID
            user_id: The user's ID (ownership check)
            
        Returns:
            True if refreshed, False if not found
        """
        return refresh_memory(memory_id, user_id)

    # =========================================================================
    # Formatting
    # =========================================================================

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

    @staticmethod
    def get_memory_stats(user_id: int) -> dict:
        """
        Get statistics about user's memories.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dict with counts by type, stale count, etc.
        """
        all_memories = MemoryService.get_all_memories(user_id)
        stale_memories = MemoryService.get_stale_memories(user_id)
        
        by_type = {}
        total_references = 0
        
        for mem in all_memories:
            if mem.memory_type not in by_type:
                by_type[mem.memory_type] = 0
            by_type[mem.memory_type] += 1
            total_references += mem.reference_count
        
        return {
            "total": len(all_memories),
            "by_type": by_type,
            "stale_count": len(stale_memories),
            "total_references": total_references,
        }
