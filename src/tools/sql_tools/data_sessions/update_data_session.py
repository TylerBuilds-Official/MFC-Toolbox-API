"""
Updates a data session.
"""
import json
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def update_data_session(session_id: int, user_id: int, updates: dict) -> bool:
    """
    Updates a data session with the provided fields.
    
    Allowed update fields:
        - status: str
        - error_message: str
        - visualization_config: dict
        - tool_params: dict
    
    Args:
        session_id: The session ID to update
        user_id: The user ID (for ownership verification)
        updates: Dictionary of fields to update
        
    Returns:
        True if update succeeded, False if session not found or not owned by user.
    """
    allowed_fields = {'status', 'error_message', 'visualization_config', 'tool_params'}
    
    # Filter to only allowed fields
    filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
    
    if not filtered_updates:
        return False
    
    # Build dynamic UPDATE query
    set_clauses = []
    params = []
    
    for field, value in filtered_updates.items():
        if field in ('visualization_config', 'tool_params'):
            # JSON fields
            set_clauses.append(f"{snake_to_pascal(field)} = ?")
            params.append(json.dumps(value) if value else None)
        else:
            set_clauses.append(f"{snake_to_pascal(field)} = ?")
            params.append(value)
    
    # Always update UpdatedAt
    set_clauses.append("UpdatedAt = GETDATE()")
    
    # Add WHERE params
    params.extend([session_id, user_id])
    
    query = f"""
        UPDATE {SCHEMA}.DataSessions
        SET {', '.join(set_clauses)}
        WHERE Id = ? AND UserId = ?
    """
    
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows_affected = cursor.rowcount
        cursor.close()
        
        return rows_affected > 0


def update_data_session_status(
    session_id: int, 
    status: str, 
    error_message: str = None
) -> bool:
    """
    Convenience function to update just the status (and optional error message).
    Does NOT verify user ownership - use for internal execution updates.
    
    Args:
        session_id: The session ID
        status: New status (pending, running, success, error)
        error_message: Optional error message (typically set when status='error')
        
    Returns:
        True if update succeeded.
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            UPDATE {SCHEMA}.DataSessions
            SET Status = ?, ErrorMessage = ?, UpdatedAt = GETDATE()
            WHERE Id = ?
            """,
            (status, error_message, session_id)
        )
        rows_affected = cursor.rowcount
        cursor.close()
        
        return rows_affected > 0


def snake_to_pascal(name: str) -> str:
    """Convert snake_case to PascalCase for SQL column names."""
    return ''.join(word.capitalize() for word in name.split('_'))
