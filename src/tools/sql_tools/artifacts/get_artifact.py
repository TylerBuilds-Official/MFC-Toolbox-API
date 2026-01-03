"""
Retrieves an artifact by ID.
Calls Toolbox_GetArtifactById stored procedure.
"""
import json
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_artifact(artifact_id: str, user_id: int = None) -> dict | None:
    """
    Retrieves an artifact by UUID.
    Optionally filters by user_id for ownership verification.
    
    Args:
        artifact_id: UUID string of the artifact
        user_id: Optional user ID for ownership check
        
    Returns:
        Dictionary with artifact fields, or None if not found.
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"EXEC {SCHEMA}.Toolbox_GetArtifactById @ArtifactId = ?, @UserId = ?",
            (artifact_id, user_id)
        )
        
        row = cursor.fetchone()
        cursor.close()
        
        if row is None:
            return None
        
        return {
            'id':                 str(row[0]),
            'user_id':            row[1],
            'conversation_id':    row[2],
            'message_id':         row[3],
            'artifact_type':      row[4],
            'title':              row[5],
            'generation_params':  json.loads(row[6]) if row[6] else None,
            'generation_results': json.loads(row[7]) if row[7] else None,
            'status':             row[8],
            'error_message':      row[9],
            'created_at':         row[10],
            'updated_at':         row[11],
            'accessed_at':        row[12],
            'access_count':       row[13],
            'metadata':           json.loads(row[14]) if row[14] else None,
        }
