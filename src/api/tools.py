from fastapi import Depends, APIRouter
from src.tools.auth import User, get_current_user
from src.tools.tool_registry import get_chat_tools, get_chat_toolbox_tools, get_data_tools


router = APIRouter()

@router.get("/tools")
async def get_tools(
        surface: str = None,
        user: User = Depends(get_current_user)
):
    """
    Get available tools, filtered by user role and optional surface.

    Args:
        surface: Optional filter for tool visibility
            - None or "ai": All tools for AI (default)
            - "chat_toolbox": Tools for chat sidebar UI
            - "data": Tools for data visualization page
    """
    if surface == "chat_toolbox":
        return {"tools": get_chat_toolbox_tools(user.role)}
    elif surface == "data":
        return {"tools": get_data_tools(user.role)}
    else:
        # Default: all tools for AI
        return {"tools": get_chat_tools(user.role)}