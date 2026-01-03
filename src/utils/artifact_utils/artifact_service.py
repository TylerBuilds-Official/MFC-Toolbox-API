"""
Service layer for Artifact operations.

Handles business logic for creating, retrieving, and managing artifacts.
Coordinates between SQL layer and API layer.
"""

from src.tools.sql_tools import (
    create_artifact as sql_create_artifact,
    get_artifact as sql_get_artifact,
    get_artifacts_by_user as sql_get_artifacts_by_user,
    get_artifacts_by_conversation as sql_get_artifacts_by_conversation,
    record_artifact_access as sql_record_artifact_access,
    update_artifact_metadata as sql_update_artifact_metadata,
    update_artifact_status as sql_update_artifact_status,
    update_artifact_generation_results as sql_update_artifact_generation_results,
    create_data_session_from_artifact as sql_create_data_session_from_artifact,
    get_existing_session_for_artifact as sql_get_existing_session_for_artifact,
)

from src.utils.artifact_utils.artifact import (
    Artifact,
    ArtifactGenerationParams,
    ArtifactGenerationResults,
    ArtifactType,
    ArtifactStatus,
)


class ArtifactService:
    """
    Service for artifact operations.
    
    Usage:
        artifact = ArtifactService.create_artifact(...)
        artifact = ArtifactService.get_artifact(artifact_id, user_id)
        session  = ArtifactService.open_artifact(artifact_id, user_id)
    """

    @staticmethod
    def create_artifact(
        user_id: int,
        conversation_id: int,
        artifact_type: ArtifactType,
        title: str,
        generation_params: ArtifactGenerationParams,
        generation_results: ArtifactGenerationResults = None,
        message_id: int = None,
        status: ArtifactStatus = 'ready',
        metadata: dict = None
    ) -> Artifact:
        """
        Creates a new artifact.
        
        Args:
            user_id: Owner of the artifact
            conversation_id: Conversation this artifact belongs to
            artifact_type: Type of artifact (data, word, excel, pdf, image)
            title: Display title for the artifact card
            generation_params: Recipe for recreating the artifact
            generation_results: Optional summary of initial execution
            message_id: Optional message ID if embedded in a message
            status: Initial status (default 'ready')
            metadata: Optional type-specific metadata
            
        Returns:
            Artifact object
        """
        data = sql_create_artifact(
            user_id           = user_id,
            conversation_id   = conversation_id,
            artifact_type     = artifact_type,
            title             = title,
            generation_params = generation_params.to_dict(),
            generation_results = generation_results.to_dict() if generation_results else None,
            message_id        = message_id,
            status            = status,
            metadata          = metadata,
        )
        return ArtifactService._dict_to_artifact(data)

    @staticmethod
    def get_artifact(artifact_id: str, user_id: int = None) -> Artifact | None:
        """
        Retrieves an artifact by ID.
        
        Args:
            artifact_id: UUID string of the artifact
            user_id: Optional user ID for ownership verification
            
        Returns:
            Artifact object or None if not found
        """
        data = sql_get_artifact(artifact_id, user_id)
        if data is None:
            return None
        return ArtifactService._dict_to_artifact(data)

    @staticmethod
    def list_artifacts_by_user(
        user_id: int,
        artifact_type: ArtifactType = None,
        limit: int = 50,
        offset: int = 0
    ) -> list[Artifact]:
        """
        Lists artifacts for a user with optional filtering.
        
        Returns:
            List of Artifact objects, ordered by CreatedAt DESC
        """
        data_list = sql_get_artifacts_by_user(user_id, artifact_type, limit, offset)
        return [ArtifactService._dict_to_artifact(d) for d in data_list]

    @staticmethod
    def list_artifacts_by_conversation(
        conversation_id: int,
        user_id: int = None
    ) -> list[Artifact]:
        """
        Lists all artifacts in a conversation.
        
        Returns:
            List of Artifact objects, ordered by CreatedAt ASC
        """
        data_list = sql_get_artifacts_by_conversation(conversation_id, user_id)
        return [ArtifactService._dict_to_artifact(d) for d in data_list]

    @staticmethod
    def open_artifact(artifact_id: str, user_id: int, force_new: bool = False) -> dict:
        """
        Opens an artifact - the main click handler.
        
        Flow:
        1. Check if DataSession already exists for this artifact
        2. If exists and not force_new, return existing session
        3. If not exists or force_new, create new DataSession
        4. Record artifact access
        
        Args:
            artifact_id: UUID string of the artifact
            user_id: User ID for ownership verification
            force_new: If True, always create new session (right-click "Open in New Session")
            
        Returns:
            Dict with 'session_id' and 'is_new' flag
            
        Raises:
            ValueError if artifact not found or not owned
        """
        # Check for existing session (unless forcing new)
        if not force_new:
            existing = sql_get_existing_session_for_artifact(artifact_id, user_id)
            if existing and existing['status'] == 'success':
                # Record access but return existing session
                sql_record_artifact_access(artifact_id)
                return {
                    'session_id': existing['id'],
                    'is_new':     False,
                }
        
        # Create new session from artifact
        session_data = sql_create_data_session_from_artifact(artifact_id, user_id)
        
        if session_data is None:
            raise ValueError(f"Artifact {artifact_id} not found or not owned by user {user_id}")
        
        return {
            'session_id': session_data['id'],
            'is_new':     True,
        }

    @staticmethod
    def update_results(
        artifact_id: str,
        row_count: int,
        column_count: int,
        columns: list[str] = None
    ) -> bool:
        """
        Updates artifact with execution results summary.
        Called after initial tool execution during artifact creation.
        
        Returns:
            True if update succeeded
        """
        results = ArtifactGenerationResults.success(row_count, column_count, columns)
        return sql_update_artifact_generation_results(artifact_id, results.to_dict())

    @staticmethod
    def mark_error(artifact_id: str, error_message: str) -> bool:
        """
        Marks artifact as failed with error message.
        
        Returns:
            True if update succeeded
        """
        sql_update_artifact_generation_results(
            artifact_id,
            ArtifactGenerationResults.failure(error_message).to_dict()
        )
        return sql_update_artifact_status(artifact_id, 'error', error_message)

    @staticmethod
    def _dict_to_artifact(data: dict) -> Artifact:
        """Convert raw dict from SQL to Artifact object."""
        gen_params = None
        if data.get('generation_params'):
            gen_params = ArtifactGenerationParams.from_dict(data['generation_params'])
        
        gen_results = None
        if data.get('generation_results'):
            gen_results = ArtifactGenerationResults.from_dict(data['generation_results'])
        
        return Artifact(
            id                 = data['id'],
            user_id            = data['user_id'],
            conversation_id    = data['conversation_id'],
            message_id         = data.get('message_id'),
            artifact_type      = data['artifact_type'],
            title              = data['title'],
            generation_params  = gen_params,
            generation_results = gen_results,
            status             = data['status'],
            error_message      = data.get('error_message'),
            created_at         = data['created_at'],
            updated_at         = data['updated_at'],
            accessed_at        = data.get('accessed_at'),
            access_count       = data.get('access_count', 0),
            metadata           = data.get('metadata'),
        )
