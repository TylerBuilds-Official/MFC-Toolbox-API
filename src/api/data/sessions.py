from fastapi import APIRouter, HTTPException, Depends

from src.utils.data_utils import DataSessionService, DataResultService, DataExecutionService
from src.utils._dataclasses_main.create_data_session_request import CreateDataSessionRequest
from src.utils._dataclasses_main.update_data_session_request import UpdateDataSessionRequest

from src.tools.auth import User, require_active_user



router = APIRouter()


_data_execution_service = DataExecutionService()


@router.post("/data/sessions")
async def create_data_session(body: CreateDataSessionRequest,
                              user: User = Depends(require_active_user)):

    """
    Create a new data session (draft, not executed).

    Returns session with status='pending'.
    Call POST /data/sessions/{id}/execute to run the tool.
    """
    session = DataSessionService.create_session(
        user_id=user.id,
        tool_name=body.tool_name,
        tool_params=body.tool_params,
        message_id=body.message_id,
        parent_session_id=body.parent_session_id,
        visualization_config=body.visualization_config)

    return session.to_dict()


@router.delete("/data/sessions/{session_id}")
async def delete_data_session(session_id: int,
                              user: User = Depends(require_active_user)):

    """ Delete a data session """

    success = DataSessionService.delete_session(session_id, user.id)

    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"success": True, "message": "Session deleted"}


@router.get("/data/sessions")
async def list_data_sessions(limit: int = 50, offset: int = 0,
                             tool_name: str = None, status: str = None,
                             group_id: int = None, ungrouped: bool = False,
                             user: User = Depends(require_active_user)):

    """List data sessions for current user with optional filtering.
    
    Query params:
        limit: Max number of results (default 50)
        offset: Pagination offset (default 0)
        tool_name: Filter by tool name
        status: Filter by status
        group_id: Filter by group ID (returns sessions in that group)
        ungrouped: If true, return only sessions with no group
    """

    sessions = DataSessionService.list_sessions(
        user_id=user.id,
        limit=limit,
        offset=offset,
        tool_name=tool_name,
        status=status,
        group_id=group_id,
        ungrouped=ungrouped)

    return {
        "sessions": [s.to_dict() for s in sessions],
        "count": len(sessions)
    }


@router.get("/data/sessions/{session_id}")
async def get_data_session(session_id: int,
                           user: User = Depends(require_active_user)):

    """Get a specific data session with has_results flag."""

    result = DataSessionService.get_session_with_has_results(session_id, user.id)

    if result is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return result


@router.patch("/data/sessions/{session_id}")
async def update_data_session(session_id: int, body: UpdateDataSessionRequest,
                              user: User = Depends(require_active_user)):

    """Update session visualization config or other fields."""

    updates = {}

    if body.visualization_config is not None:
        updates["visualization_config"] = body.visualization_config

    if body.status is not None:
        updates["status"] = body.status

    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")

    session = DataSessionService.update_session(session_id, user.id, updates)

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return session.to_dict()


@router.delete("/data/sessions/{session_id}")
async def delete_data_session(session_id: int,
                              user: User = Depends(require_active_user)):

    """Soft delete a data session (sets IsActive = 0)."""

    success = DataSessionService.delete_session(session_id, user.id)

    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"success": True, "message": "Session deleted"}


@router.post("/data/sessions/{session_id}/execute")
async def execute_data_session(session_id: int,
                               user: User = Depends(require_active_user)):

    """
    Execute the tool for a session and store results.

    Flow:
    1. Verify user has permission for the tool
    2. Sets status to 'running'
    3. Executes the MCP tool
    4. Normalizes and stores results
    5. Sets status to 'success' or 'error'

    Returns the updated session and result (if successful).
    """

    # Verify ownership
    session = DataSessionService.get_session(session_id, user.id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        updated_session, result = _data_execution_service.execute(session_id, user.role)

        response = {
            "session": updated_session.to_dict(),
            "success": updated_session.status == "success"
        }

        if result:
            response["result"] = result.to_dict()

        return response

    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")


@router.get("/data/sessions/{session_id}/results")
async def get_data_session_results(session_id: int,
                                   user: User = Depends(require_active_user)):

    """Get the result payload for a session."""

    # Verify ownership
    session = DataSessionService.get_session(session_id, user.id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    result = DataResultService.get_result(session_id)

    if result is None:
        raise HTTPException(status_code=404, detail="No results found for session")

    return result.to_dict()


@router.get("/data/sessions/groups/{group_id}")
async def get_data_session_group(group_id: int,
                                 user: User = Depends(require_active_user)):

    """Get all sessions in a lineage group."""

    sessions = DataSessionService.get_session_lineage(group_id, user.id)

    if not sessions:
        raise HTTPException(status_code=404, detail="Session group not found")

    return {
        "group_id": group_id,
        "sessions": [s.to_dict() for s in sessions],
        "count": len(sessions)
    }