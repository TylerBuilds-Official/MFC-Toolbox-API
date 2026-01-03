"""
Records an artifact access (click/open).
Calls Toolbox_RecordArtifactAccess stored procedure.
"""
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def record_artifact_access(artifact_id: str) -> bool:
    """
    Records that an artifact was accessed.
    Increments AccessCount, updates AccessedAt, sets Status to 'opened'.
    
    Args:
        artifact_id: UUID string of the artifact
        
    Returns:
        True if update succeeded, False if artifact not found.
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"EXEC {SCHEMA}.Toolbox_RecordArtifactAccess @ArtifactId = ?",
            (artifact_id,)
        )
        
        # Check if any rows were affected
        row = cursor.fetchone()
        cursor.close()
        
        # Stored proc returns 1 row on success
        return row is not None
