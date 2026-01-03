"""
Retrieves all artifacts in a conversation.
Calls Toolbox_GetArtifactsByConversation stored procedure.
"""
import json
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_artifacts_by_conversation(conversation_id: int, user_id: int = None) -> list[dict]:
    """
    Retrieves all artifacts in a conversation.
    Optionally filters by user_id for ownership verification.
    
    Args:
        conversation_id: The conversation ID
        user_id: Optional user ID for ownership check
        
    Returns:
        List of artifact dictionaries, ordered by CreatedAt ASC.
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"EXEC {SCHEMA}.Toolbox_GetArtifactsByConversation "
            f"@ConversationId = ?, @UserId = ?",
            (conversation_id, user_id)
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
