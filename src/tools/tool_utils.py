"""
Tool Utilities

Functions and classes for working with the tool registry.
Handles:
- Permission checking (role-based AND specialty-based)
- Tool lookup and filtering
- Tool execution dispatch (sync and async)
- Context injection (user_id, conversation_id)
"""
import asyncio
from typing import Callable, Any

from src.tools.tool_registry import (
    TOOL_REGISTRY,
    TOOL_CATEGORIES,
    ROLE_HIERARCHY,
    SPECIALTY_CATEGORIES,
)


# =============================================================================
# Role & Permission Helpers
# =============================================================================

def get_role_level(role: str) -> int:
    """Get numeric level for a role. Returns 0 for unknown roles."""
    return ROLE_HIERARCHY.get(role, 0)


def can_use_tool(user_role: str, tool_category: str, user_specialties: list[str] = None) -> bool:
    """
    Check if a user has permission to use tools in a category.
    
    Permission can be granted via:
    1. Base role hierarchy (user_role level >= category's required level)
    2. Specialty grant (user has a specialty that unlocks this category)
    
    Args:
        user_role: The user's base role (e.g., "user", "admin")
        tool_category: The tool's category (e.g., "job_read", "transmittal_processing")
        user_specialties: List of specialty roles the user has (e.g., ["drawing_coordinator"])
        
    Returns:
        True if user has sufficient permissions via role OR specialty
    """
    # Check 1: Role-based permission (existing hierarchy)
    if tool_category in TOOL_CATEGORIES:
        required_role = TOOL_CATEGORIES[tool_category]
        user_level = get_role_level(user_role)
        required_level = get_role_level(required_role)
        if user_level >= required_level:
            return True
    
    # Check 2: Specialty-based permission (additive)
    if user_specialties:
        for specialty in user_specialties:
            specialty_categories = SPECIALTY_CATEGORIES.get(specialty, [])
            if tool_category in specialty_categories:
                return True
    
    # Check 3: Admin override - admins can use everything
    if get_role_level(user_role) >= get_role_level("admin"):
        return True
    
    return False


# =============================================================================
# Tool Lookup Helpers
# =============================================================================

def get_tool(tool_name: str) -> dict | None:
    """Get a tool definition by name."""
    for tool in TOOL_REGISTRY:
        if tool["name"] == tool_name:
            return tool
    return None


def get_executor(tool_name: str) -> Callable | None:
    """Get the executor function for a tool."""
    tool = get_tool(tool_name)
    if tool:
        return tool.get("executor")
    return None


def get_all_tool_names() -> list[str]:
    """Get list of all tool names (for validation, etc.)"""
    return [tool["name"] for tool in TOOL_REGISTRY]


# =============================================================================
# Tool Filtering for Different Contexts
# =============================================================================

def get_chat_tools(user_role: str, user_specialties: list[str] = None) -> list[dict]:
    """
    Get tools formatted for OpenAI/Anthropic function calling.
    Filtered by user's permission level and specialties.
    
    This is for the AI - it sees ALL permitted tools.
    
    Args:
        user_role: The user's base role
        user_specialties: List of specialty roles the user has
        
    Returns:
        List of tools in OpenAI function format
    """
    tools = []
    for tool in TOOL_REGISTRY:
        if can_use_tool(user_role, tool["category"], user_specialties):
            tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                }
            })
    return tools


def get_chat_toolbox_tools(user_role: str, user_specialties: list[str] = None) -> list[dict]:
    """
    Get tools for the chat sidebar UI toolbox.
    Filtered by permission AND chat_toolbox visibility flag.
    
    Only includes tools users should manually trigger (not AI-internal tools).
    
    Args:
        user_role: The user's base role
        user_specialties: List of specialty roles the user has
        
    Returns:
        List of tools in simplified format for UI, with display_category for grouping
    """
    tools = []
    for tool in TOOL_REGISTRY:
        # Must be visible in chat toolbox (default True)
        if not tool.get("chat_toolbox", True):
            continue
        # Must have permission
        if not can_use_tool(user_role, tool["category"], user_specialties):
            continue
        
        # Convert parameters to simpler format for frontend
        simple_params = _convert_params_to_simple(tool["parameters"])
        
        tool_entry = {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": simple_params,
            "display_category": tool.get("display_category", "Other"),
        }
        
        # Include data viz info if available (for potential charting)
        if tool.get("data_visualization"):
            tool_entry["data_visualization"] = True
            tool_entry["default_chart_type"] = tool.get("default_chart_type", "table")
            if tool.get("chart_config"):
                tool_entry["chart_config"] = tool["chart_config"]
        
        tools.append(tool_entry)
    
    return tools


def get_data_tools(user_role: str, user_specialties: list[str] = None) -> list[dict]:
    """
    Get tools available for data visualization page.
    Only includes tools with data_visualization=True, filtered by permission.
    
    Args:
        user_role: The user's base role
        user_specialties: List of specialty roles the user has
        
    Returns:
        List of tools in simplified format for data page, with display_category for grouping
    """
    tools = []
    for tool in TOOL_REGISTRY:
        # Must be data-visualizable and user must have permission
        if not tool.get("data_visualization", False):
            continue
        if not can_use_tool(user_role, tool["category"], user_specialties):
            continue
            
        # Convert parameters to simpler format for frontend
        simple_params = _convert_params_to_simple(tool["parameters"])
        
        tool_entry = {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": simple_params,
            "display_category": tool.get("display_category", "Other"),
            "default_chart_type": tool.get("default_chart_type", "table"),
        }
        
        # Include chart config if present
        if tool.get("chart_config"):
            tool_entry["chart_config"] = tool["chart_config"]
        
        tools.append(tool_entry)
    
    return tools


def _convert_params_to_simple(openai_params: dict) -> list[dict]:
    """
    Convert OpenAI parameter format to simple list format for frontend.
    
    OpenAI format:
        {"type": "object", "properties": {"job_number": {"type": "string", ...}}, "required": [...]}
    
    Simple format:
        [{"name": "job_number", "type": "string", "required": True, "description": "..."}]
    """
    properties = openai_params.get("properties", {})
    required = openai_params.get("required", [])
    
    params = []
    for name, spec in properties.items():
        params.append({
            "name": name,
            "type": spec.get("type", "string"),
            "required": name in required,
            "description": spec.get("description", ""),
        })
    
    return params


# =============================================================================
# Tool Dispatcher Class
# =============================================================================

class ToolDispatcher:
    """
    Tool dispatcher for LLM function calling.
    
    Handles routing tool calls to their executors and injecting
    server-side context (like user_id) for tools that need it.
    
    Supports both sync and async tools. Use dispatch_async() when
    calling from async context to properly await async tools.
    """
    
    def _prepare_dispatch(self, name: str, context: dict = None, **kwargs) -> tuple[Callable | None, dict]:
        """
        Common preparation for dispatch - checks permissions, injects context.
        
        Returns:
            Tuple of (executor, kwargs) or (None, error_dict)
        """
        # Get tool definition from registry
        tool_def = get_tool(name)
        
        if not tool_def:
            return None, {"error": f"Tool '{name}' not found."}
        
        executor = tool_def.get("executor")
        if not executor:
            return None, {"error": f"Tool '{name}' has no executor defined."}

        # Permission check (defense in depth)
        user_role = context.get("user_role", "pending") if context else "pending"
        user_specialties = context.get("user_specialties", []) if context else []
        
        if not can_use_tool(user_role, tool_def["category"], user_specialties):
            return None, {
                "error": f"Permission denied: insufficient privileges for tool '{name}'."
            }

        # Inject context based on tool metadata
        if context:
            if tool_def.get("needs_user_id") and "user_id" in context:
                kwargs["user_id"] = context["user_id"]
            if tool_def.get("needs_conversation_id") and "conversation_id" in context:
                kwargs["conversation_id"] = context["conversation_id"]

        return executor, kwargs

    def dispatch(self, name: str, context: dict = None, **kwargs) -> Any:
        """
        Dispatch a tool call to its executor (sync version).
        
        WARNING: This will NOT properly handle async tools!
        Use dispatch_async() from async contexts.

        Args:
            name: Name of the tool to execute
            context: Server-side context (user_id, user_role, conversation_id, etc.)
            **kwargs: Tool parameters from LLM

        Returns:
            Tool execution result
        """
        executor, prepared_kwargs = self._prepare_dispatch(name, context, **kwargs)
        
        if executor is None:
            return prepared_kwargs  # This is the error dict
        
        # Check if tool is async
        tool_def = get_tool(name)
        if tool_def and tool_def.get("is_async"):
            # Try to run in event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Can't await from sync context when loop is running
                    return {"error": f"Tool '{name}' is async and must be called from async context. Use dispatch_async()."}
                else:
                    return loop.run_until_complete(executor(**prepared_kwargs))
            except RuntimeError:
                return asyncio.run(executor(**prepared_kwargs))
        
        return executor(**prepared_kwargs)

    async def dispatch_async(self, name: str, context: dict = None, **kwargs) -> Any:
        """
        Dispatch a tool call to its executor (async version).
        
        Use this from async contexts to properly handle async tools.

        Args:
            name: Name of the tool to execute
            context: Server-side context (user_id, user_role, conversation_id, etc.)
            **kwargs: Tool parameters from LLM

        Returns:
            Tool execution result
        """
        executor, prepared_kwargs = self._prepare_dispatch(name, context, **kwargs)
        
        if executor is None:
            return prepared_kwargs  # This is the error dict
        
        # Check if tool is async
        tool_def = get_tool(name)
        if tool_def and tool_def.get("is_async"):
            return await executor(**prepared_kwargs)
        else:
            # Run sync tool in executor to not block event loop
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: executor(**prepared_kwargs))
    
    def is_async_tool(self, name: str) -> bool:
        """Check if a tool requires async execution."""
        tool_def = get_tool(name)
        return tool_def.get("is_async", False) if tool_def else False


# Backwards compatibility alias
OAToolBase = ToolDispatcher
