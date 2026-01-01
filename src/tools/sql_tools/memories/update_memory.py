from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def update_memory(memory_id: int, user_id: int, updates: dict) -> bool:
    """
    Update a memory's content or type.
    
    Args:
        memory_id: The memory's ID
        user_id: The user's ID (for ownership validation)
        updates: Dictionary of fields to update (content, memory_type)
        
    Returns:
        True if updated, False if not found
    """
    allowed_fields = {"content": "Content", "memory_type": "MemoryType"}
    
    set_clauses = []
    params = []
    
    for key, value in updates.items():
        if key in allowed_fields:
            set_clauses.append(f"{allowed_fields[key]} = ?")
            params.append(value)
    
    if not set_clauses:
        return False
    
    # Always update UpdatedAt
    set_clauses.append("UpdatedAt = GETDATE()")
    
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
