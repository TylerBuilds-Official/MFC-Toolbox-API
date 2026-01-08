from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def update_memory(memory_id: int, user_id: int, updates: dict) -> bool:
    """
    Update a memory's content, type, or expiration.
    
    Args:
        memory_id: The memory's ID
        user_id: The user's ID (for ownership validation)
        updates: Dictionary of fields to update:
            - content: New content text
            - memory_type: New type
            - expires_at: New expiration (datetime string or None to clear)
        
    Returns:
        True if updated, False if not found
    """
    allowed_fields = {
        "content": "Content", 
        "memory_type": "MemoryType",
        "expires_at": "ExpiresAt"
    }
    
    set_clauses = []
    params = []
    
    for key, value in updates.items():
        if key in allowed_fields:
            set_clauses.append(f"{allowed_fields[key]} = ?")
            params.append(value)
    
    if not set_clauses:
        return False
    
    # Always update UpdatedAt
    set_clauses.append("UpdatedAt = GETUTCDATE()")
    
    # Add WHERE params
    params.extend([memory_id, user_id])
    
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            UPDATE {SCHEMA}.UserMemories
            SET {', '.join(set_clauses)}
            WHERE Id = ? AND UserId = ?
            """,
            params
        )
        
        rows_affected = cursor.rowcount
        cursor.close()
        
        return rows_affected > 0


def refresh_memory(memory_id: int, user_id: int) -> bool:
    """
    Refresh a memory's staleness by updating LastReferencedAt.
    Used when user explicitly confirms a memory is still relevant.
    
    Args:
        memory_id: The memory's ID
        user_id: The user's ID (for ownership validation)
        
    Returns:
        True if refreshed, False if not found
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            UPDATE {SCHEMA}.UserMemories
            SET LastReferencedAt = GETUTCDATE(),
                UpdatedAt = GETUTCDATE()
            WHERE Id = ? AND UserId = ? AND IsActive = 1
            """,
            (memory_id, user_id)
        )
        
        rows_affected = cursor.rowcount
        cursor.close()
        
        return rows_affected > 0
