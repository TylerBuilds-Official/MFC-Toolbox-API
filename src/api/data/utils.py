from fastapi import Depends, APIRouter
from src.tools.auth import User, require_active_user
from src.utils.data_utils import DataExecutionService

_data_execution_service = DataExecutionService()
router = APIRouter()

@router.get("/data/tools")
async def get_data_tools_endpoint(user: User = Depends(require_active_user)):
    """Get list of tools available for data visualization, filtered by user role."""
    return {"tools": _data_execution_service.get_available_tools(user.role)}
