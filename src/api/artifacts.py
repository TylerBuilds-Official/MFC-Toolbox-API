from fastapi import APIRouter, HTTPException, Depends
from src.tools.auth import User, require_active_user
from src.utils.artifact_utils import ArtifactService
from src.utils.conversation_utils import ConversationService
from src.utils.data_utils import DataExecutionService

_data_execution_service = DataExecutionService()

router = APIRouter()

@router.get("/artifacts/{artifact_id}")
async def get_artifact(
        artifact_id: str,
        user: User = Depends(require_active_user)
):
    """
    Get an artifact by ID.

    Returns artifact details including generation params and results summary.
    """
    artifact = ArtifactService.get_artifact(artifact_id, user.id)

    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found")

    return artifact.to_dict()


@router.post("/artifacts/{artifact_id}/open")
async def open_artifact(
        artifact_id: str,
        force_new: bool = False,
        user: User = Depends(require_active_user)
):
    """
    Open an artifact - creates or retrieves a DataSession and executes it.

    This is the click handler for artifact cards in chat.

    Flow:
    1. If DataSession exists for this artifact (and not force_new), return it
    2. Otherwise, create new DataSession from artifact recipe
    3. Execute the tool immediately
    4. Record artifact access (increment counter, update accessed_at)

    Args:
        artifact_id: UUID of the artifact
        force_new: If True, always create new session (for "Open in New Session")
        user: User object for the current user

    Returns:
        session_id: ID of the DataSession to navigate to
        is_new: Whether a new session was created
    """
    try:
        result = ArtifactService.open_artifact(artifact_id, user.id, force_new)

        # If new session, execute it immediately
        if result['is_new']:
            try:
                _data_execution_service.execute(result['session_id'], user.role)
            except Exception as e:
                # Log but don't fail - user can still see session and retry
                print(f"[open_artifact] Auto-execute failed: {e}")

        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/conversations/{conversation_id}/artifacts")
async def get_conversation_artifacts(
        conversation_id: int,
        user: User = Depends(require_active_user)
):
    """
    Get all artifacts in a conversation.

    Returns artifacts in creation order (ASC).
    """
    # Verify conversation ownership
    conversation = ConversationService.get_conversation(conversation_id, user.id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    artifacts = ArtifactService.list_artifacts_by_conversation(conversation_id, user.id)

    return {
        "conversation_id": conversation_id,
        "artifacts": [a.to_dict() for a in artifacts],
        "count": len(artifacts)
    }


@router.get("/artifacts")
async def list_user_artifacts(
        artifact_type: str = None,
        limit: int = 50,
        offset: int = 0,
        user: User = Depends(require_active_user)
):
    """
    List all artifacts for the current user.

    Args:
        artifact_type: Optional filter (data, word, excel, pdf, image)
        limit: Max results (default 50)
        offset: Pagination offset

    Returns artifacts in reverse creation order (newest first).
    """
    artifacts = ArtifactService.list_artifacts_by_user(
        user_id=user.id,
        artifact_type=artifact_type,
        limit=limit,
        offset=offset
    )

    return {
        "artifacts": [a.to_dict() for a in artifacts],
        "count": len(artifacts)
    }
