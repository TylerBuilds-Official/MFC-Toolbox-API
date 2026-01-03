"""
Retrieves artifacts for a user with optional filtering.
Calls Toolbox_GetArtifactsByUser stored procedure.
"""
import json
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_artifacts_by_user(
    user_id: int,
    artifact_type: str = None,
    limit: int = 50,
    offset: int = 0
) -> list[dict]:
    """
    Retrieves artifacts for a user with optional type filtering and pagination.
    
    Args:
        user_id: The user's ID
        artifact_type: Optional filter by type (data, word, excel, pdf, image)
        limit: Maximum results to return (default 50)
        offset: Number of results to skip (default 0)
        
    Returns:
        List of artifact dictionaries, ordered by CreatedAt DESC.
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"EXEC {SCHEMA}.Toolbox_GetArtifactsByUser "
            f"@UserId = ?, @ArtifactType = ?, @Limit = ?, @Offset = ?",
            (user_id, artifact_type, limit, offset)
        )
        
        rows = cursor.fetchall()
        cursor.close()
        
        return [_row_to_dict(row) for row in rows]


def _row_to_dict(row) -> dict:
    """Convert a result row to artifact dictionary."""
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
