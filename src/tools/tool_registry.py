"""
Centralized Tool Registry

Single source of truth for all tools available in the system.
Handles:
- Tool definitions (name, description, parameters)
- Permission categories
- Execution routing
- Data visualization flags
"""
from typing import Callable, Any

# =============================================================================
# Role Hierarchy
# =============================================================================
# Higher number = more permissions
# A role can access anything at or below its level

ROLE_HIERARCHY = {
    "pending": 0,    # Newly registered, awaiting approval
    "user": 10,      # Standard user
    "admin": 500,    # Full access
}


# =============================================================================
# Tool Categories
# =============================================================================
# Maps category name to minimum role required

TOOL_CATEGORIES = {
    "job_read": "user",        # View job data
    "job_write": "admin",      # Modify job data (future)
    "reports": "user",         # Run reports
    "admin_tools": "admin",    # System administration
}


# =============================================================================
# Tool Registry
# =============================================================================
# Import executors here to keep registry self-contained
from src.tools.local_mcp_tools.local_mcp_tool_getAllJobInfo import oa_get_jobs
from src.tools.local_mcp_tools.local_mcp_tool_getJobInfo import oa_get_job_info


TOOL_REGISTRY: list[dict] = [
    {
        # Identity
        "name": "get_all_job_info",
        "description": "Get a list of all jobs with basic info (job number, name, contractor, location, etc.)",
        
        # Permissions
        "category": "job_read",
        
        # Parameters (OpenAI function calling format)
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },
        
        # Execution
        "executor": oa_get_jobs,
        
        # Data visualization
        "data_visualization": True,
        "default_chart_type": "table",
        "normalizer": "job_list",  # Custom normalizer key (optional)
    },
    {
        # Identity
        "name": "get_job_info",
        "description": "Get detailed information about a specific job by job number.",
        
        # Permissions
        "category": "job_read",
        
        # Parameters (OpenAI function calling format)
        "parameters": {
            "type": "object",
            "properties": {
                "job_number": {
                    "type": "string",
                    "description": "The job number to retrieve information for (e.g. 6516)"
                }
            },
            "required": ["job_number"]
        },
        
        # Execution
        "executor": oa_get_job_info,
        
        # Data visualization
        "data_visualization": True,
        "default_chart_type": "detail",
        "normalizer": "single_job",
    },
]


# =============================================================================
# Helper Functions
# =============================================================================

def get_role_level(role: str) -> int:
    """Get numeric level for a role. Returns 0 for unknown roles."""
    return ROLE_HIERARCHY.get(role, 0)


def can_use_tool(user_role: str, tool_category: str) -> bool:
    """
    Check if a user role has permission to use tools in a category.
    
    Args:
        user_role: The user's role (e.g., "user", "admin")
        tool_category: The tool's category (e.g., "job_read")
        
    Returns:
        True if user has sufficient permissions
    """
    required_role = TOOL_CATEGORIES.get(tool_category, "admin")  # Default to admin if unknown
    user_level = get_role_level(user_role)
    required_level = get_role_level(required_role)
    return user_level >= required_level


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


def get_chat_tools(user_role: str) -> list[dict]:
    """
    Get tools formatted for OpenAI/Anthropic function calling.
    Filtered by user's permission level.
    
    Args:
        user_role: The user's role
        
    Returns:
        List of tools in OpenAI function format
    """
    tools = []
    for tool in TOOL_REGISTRY:
        if can_use_tool(user_role, tool["category"]):
            tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                }
            })
    return tools


def get_data_tools(user_role: str) -> list[dict]:
    """
    Get tools available for data visualization page.
    Only includes tools with data_visualization=True, filtered by permission.
    
    Args:
        user_role: The user's role
        
    Returns:
        List of tools in simplified format for data page
    """
    tools = []
    for tool in TOOL_REGISTRY:
        # Must be data-visualizable and user must have permission
        if not tool.get("data_visualization", False):
            continue
        if not can_use_tool(user_role, tool["category"]):
            continue
            
        # Convert parameters to simpler format for frontend
        simple_params = _convert_params_to_simple(tool["parameters"])
        
        tools.append({
            "name": tool["name"],
            "description": tool["description"],
            "parameters": simple_params,
            "default_chart_type": tool.get("default_chart_type", "table"),
        })
    
    return tools


def get_all_tool_names() -> list[str]:
    """Get list of all tool names (for validation, etc.)"""
    return [tool["name"] for tool in TOOL_REGISTRY]


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
