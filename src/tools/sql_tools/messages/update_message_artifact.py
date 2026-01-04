"""
Updates a message's ArtifactId field.
"""
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def update_message_artifact(message_id: int, artifact_id: str) -> bool:
    """
    Updates the ArtifactId field of a message.
    
    Args:
        message_id: The message to update
        artifact_id: The artifact UUID string to link
        
    Returns:
        True if update succeeded, False if message not found
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"""
            UPDATE {SCHEMA}.Messages
            SET ArtifactId = ?
            WHERE Id = ?
            """,
            (artifact_id, message_id)
        )
        
        rows_affected = cursor.rowcount
        cursor.close()
        
        return rows_affected > 0
