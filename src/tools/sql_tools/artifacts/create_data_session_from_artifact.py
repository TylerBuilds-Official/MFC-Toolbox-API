"""
Creates a DataSession from an artifact (lazy creation on click).
Calls Toolbox_CreateDataSessionFromArtifact stored procedure.
"""
import json
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def create_data_session_from_artifact(artifact_id: str, user_id: int) -> dict | None:
    """
    Creates a new DataSession from an artifact's recipe.
    This is the "lazy creation" pattern - DataSession only created when user clicks.
    
    Flow:
    1. Validates artifact exists and belongs to user
    2. Extracts tool_name, tool_params from artifact's GenerationParams
    3. Creates DataSession with ArtifactId link
    4. Records artifact access (increments counter, sets status='opened')
    5. Returns new session for immediate execution
    
    Args:
        artifact_id: UUID string of the artifact
        user_id: User ID for ownership verification and session creation
        
    Returns:
        Dictionary with new DataSession fields, or None if artifact not found/not owned.
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"EXEC {SCHEMA}.Toolbox_CreateDataSessionFromArtifact "
            f"@ArtifactId = ?, @UserId = ?",
            (artifact_id, user_id)
        )
        
        row = cursor.fetchone()
        cursor.close()
        
        if row is None:
            return None
        
        return {
            'id':                   row[0],
            'user_id':              row[1],
            'message_id':           row[2],
            'session_group_id':     row[3],
            'parent_session_id':    row[4],
            'tool_name':            row[5],
            'tool_params':          json.loads(row[6]) if row[6] else None,
            'visualization_config': json.loads(row[7]) if row[7] else None,
            'status':               row[8],
            'error_message':        row[9],
            'created_at':           row[10],
            'updated_at':           row[11],
            'artifact_id':          str(row[12]) if row[12] else None,
        }


def get_existing_session_for_artifact(artifact_id: str, user_id: int) -> dict | None:
    """
    Checks if a DataSession already exists for this artifact.
    Used for the "open existing vs create new" decision.
    
    Args:
        artifact_id: UUID string of the artifact
        user_id: User ID for ownership verification
        
    Returns:
        Most recent DataSession dict if exists, None otherwise.
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"""
            SELECT TOP 1 
                Id, UserId, MessageId, SessionGroupId, ParentSessionId,
                ToolName, ToolParams, VisualizationConfig, Status,
                ErrorMessage, CreatedAt, UpdatedAt, ArtifactId
            FROM {SCHEMA}.DataSessions
            WHERE ArtifactId = ? AND UserId = ?
            ORDER BY CreatedAt DESC
            """,
            (artifact_id, user_id)
        )
        
        row = cursor.fetchone()
        cursor.close()
        
        if row is None:
            return None
        
        return {
            'id':                   row[0],
            'user_id':              row[1],
            'message_id':           row[2],
            'session_group_id':     row[3],
            'parent_session_id':    row[4],
            'tool_name':            row[5],
            'tool_params':          json.loads(row[6]) if row[6] else None,
            'visualization_config': json.loads(row[7]) if row[7] else None,
            'status':               row[8],
            'error_message':        row[9],
            'created_at':           row[10],
            'updated_at':           row[11],
            'artifact_id':          str(row[12]) if row[12] else None,
        }
