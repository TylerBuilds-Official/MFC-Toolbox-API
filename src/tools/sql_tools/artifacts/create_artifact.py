"""
Creates a new artifact in the database.
Calls Toolbox_CreateArtifact stored procedure.
"""
import json
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def create_artifact(
    user_id: int,
    conversation_id: int,
    artifact_type: str,
    title: str,
    generation_params: dict = None,
    generation_results: dict = None,
    message_id: int = None,
    status: str = 'ready',
    metadata: dict = None
) -> dict:
    """
    Creates a new ChatArtifact record.
    
    Args:
        user_id: Owner of the artifact
        conversation_id: Conversation this artifact belongs to
        artifact_type: Type of artifact (data, word, excel, pdf, image)
        title: Display title for the artifact card
        generation_params: JSON-serializable recipe for recreating the artifact
        generation_results: JSON-serializable summary of results
        message_id: Optional message ID if artifact is embedded in a message
        status: Initial status (default 'ready')
        metadata: Optional type-specific metadata
        
    Returns:
        Dictionary with all artifact fields including the new UUID Id.

    """
    params_json  = json.dumps(generation_params) if generation_params else None
    results_json = json.dumps(generation_results) if generation_results else None
    meta_json    = json.dumps(metadata) if metadata else None
    
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"EXEC {SCHEMA}.Toolbox_CreateArtifact "
            f"@UserId = ?, @ConversationId = ?, @MessageId = ?, "
            f"@ArtifactType = ?, @Title = ?, @GenerationParams = ?, "
            f"@GenerationResults = ?, @Status = ?, @Metadata = ?",
            (user_id, conversation_id, message_id, artifact_type, title,
             params_json, results_json, status, meta_json)
        )
        
        row = cursor.fetchone()
        cursor.close()
        
        if not row:
            raise Exception("Failed to create artifact - no row returned")
        
        return {
            'id':                 str(row[0]),  # UUID as string
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
