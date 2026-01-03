"""
Updates artifact metadata and status.
"""
import json
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def update_artifact_metadata(artifact_id: str, metadata: dict) -> bool:
    """
    Updates the Metadata JSON field of an artifact.
    
    Args:
        artifact_id: UUID string of the artifact
        metadata: New metadata dictionary
        
    Returns:
        True if update succeeded, False if artifact not found.
    """
    meta_json = json.dumps(metadata) if metadata else None
    
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"EXEC {SCHEMA}.Toolbox_UpdateArtifactMetadata "
            f"@ArtifactId = ?, @Metadata = ?",
            (artifact_id, meta_json)
        )
        
        row = cursor.fetchone()
        cursor.close()
        
        return row is not None


def update_artifact_status(artifact_id: str, status: str, error_message: str = None) -> bool:
    """
    Updates the status and optional error message of an artifact.
    
    Args:
        artifact_id: UUID string of the artifact
        status: New status (ready, pending, error, opened)
        error_message: Optional error message (for status='error')
        
    Returns:
        True if update succeeded, False if artifact not found.
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"""
            UPDATE {SCHEMA}.ChatArtifacts
            SET Status = ?, ErrorMessage = ?, UpdatedAt = GETDATE()
            WHERE Id = ?
            """,
            (status, error_message, artifact_id)
        )
        
        rows_affected = cursor.rowcount
        cursor.close()
        
        return rows_affected > 0


def update_artifact_generation_results(artifact_id: str, generation_results: dict) -> bool:
    """
    Updates the GenerationResults JSON field of an artifact.
    Called after initial tool execution to store result summary.
    
    Args:
        artifact_id: UUID string of the artifact
        generation_results: Results dictionary with rowCount, columnCount, etc.
        
    Returns:
        True if update succeeded, False if artifact not found.
    """
    results_json = json.dumps(generation_results) if generation_results else None
    
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"""
            UPDATE {SCHEMA}.ChatArtifacts
            SET GenerationResults = ?, UpdatedAt = GETDATE()
            WHERE Id = ?
            """,
            (results_json, artifact_id)
        )
        
        rows_affected = cursor.rowcount
        cursor.close()
        
        return rows_affected > 0
