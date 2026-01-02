"""
Centralized Tool Registry

Single source of truth for all tools available in the system.
Handles:
- Tool definitions (name, description, parameters)
- Permission categories (category → role-based access)
- Display categories (display_category → UI grouping)
- Execution routing
- Visibility flags:
  - chat_toolbox: Show in chat sidebar UI (default True)
  - data_visualization: Show in data page (default False)
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
    "manager": 100,  # Elevated access for supervisors/managers
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
    "manager_reports": "manager",  # Sensitive reports (OT, labor costs, etc.)
    "admin_tools": "admin",    # System administration
    "memory": "user",          # Memory tools (search/save memories)
    "conversation": "user",    # Conversation tools (search/retrieve past conversations)
}


# =============================================================================
# Tool Registry
# =============================================================================
# Import executors here to keep registry self-contained
from src.tools.local_mcp_tools.local_mcp_tool_getAllJobInfo import oa_get_jobs
from src.tools.local_mcp_tools.local_mcp_tool_getJobInfo import oa_get_job_info
from src.tools.local_mcp_tools.local_mcp_tool_getMachineProductionData import oa_get_machine_production
from src.tools.local_mcp_tools.local_mcp_tool_getOTHoursByJob import oa_get_ot_hours_by_job
from src.tools.local_mcp_tools.local_mcp_tool_getOTHoursAllJobs import oa_get_ot_hours_all_jobs
from src.tools.local_mcp_tools.local_mcp_tool_getActiveJobs import oa_get_active_jobs
from src.tools.local_mcp_tools.local_mcp_tool_getJobDetails import oa_get_job_details
from src.tools.local_mcp_tools.local_mcp_tool_getJobsByPM import oa_get_jobs_by_pm
from src.tools.local_mcp_tools.local_mcp_tool_getJobsShippingSoon import oa_get_jobs_shipping_soon
from src.tools.local_mcp_tools.local_mcp_tool_searchUserMemories import oa_search_user_memories
from src.tools.local_mcp_tools.local_mcp_tool_saveUserMemory import oa_save_user_memory
from src.tools.local_mcp_tools.local_mcp_tool_searchConversations import oa_search_conversations
from src.tools.local_mcp_tools.local_mcp_tool_getRecentConversations import oa_get_recent_conversations
from src.tools.local_mcp_tools.local_mcp_tool_getConversationMessages import oa_get_conversation_messages


TOOL_REGISTRY: list[dict] = [
    {
        # Identity
        "name": "get_all_job_info",
        "description": "Get a list of all jobs with basic info (job number, name, contractor, location, etc.)",
        
        # Permissions
        "category": "job_read",
        
        # UI Display
        "display_category": "Jobs",
        
        # Parameters (OpenAI function calling format)
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },
        
        # Execution
        "executor": oa_get_jobs,
        
        # Visibility
        "chat_toolbox": True,
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
        
        # UI Display
        "display_category": "Jobs",
        
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
        
        # Visibility
        "chat_toolbox": True,
        "data_visualization": True,
        "default_chart_type": "card",
        "normalizer": "single_job",
    },
    {
        # Identity
        "name": "get_machine_production",
        "description": "Get daily production counts per CNC machine (pieces processed and total weight) over a date range.",
        
        # Permissions
        "category": "reports",
        
        # UI Display
        "display_category": "Production",
        
        # Parameters (OpenAI function calling format)
        "parameters": {
            "type": "object",
            "properties": {
                "days_back": {
                    "type": "integer",
                    "description": "Number of days to look back (default 30)"
                }
            },
            "required": []
        },
        
        # Execution
        "executor": oa_get_machine_production,
        
        # Visibility
        "chat_toolbox": True,
        "data_visualization": True,
        "default_chart_type": "line",
        "chart_config": {
            "x_axis": "ProductionDate",
            "series_by": "Machine",
            "y_axis": "PiecesProcessed",
            "y_axis_label": "Pieces Processed",
            "x_axis_label": "Date",
        },
        "normalizer": None,  # Use generic normalizer
    },
    
    # =========================================================================
    # ScheduleShare Jobs (Voltron)
    # =========================================================================
    {
        "name": "get_active_jobs",
        "description": "Get all active jobs from ScheduleShare. Optionally include on-hold jobs.",
        "category": "job_read",
        "display_category": "Jobs",
        "parameters": {
            "type": "object",
            "properties": {
                "include_on_hold": {
                    "type": "boolean",
                    "description": "Whether to include on-hold jobs (default false)"
                }
            },
            "required": []
        },
        "executor": oa_get_active_jobs,
        "chat_toolbox": True,
        "data_visualization": True,
        "default_chart_type": "table",
    },
    {
        "name": "get_job_details",
        "description": "Get comprehensive details for a specific job from ScheduleShare by job number.",
        "category": "job_read",
        "display_category": "Jobs",
        "parameters": {
            "type": "object",
            "properties": {
                "job_number": {
                    "type": "string",
                    "description": "The job number to retrieve details for (e.g. '6516')"
                }
            },
            "required": ["job_number"]
        },
        "executor": oa_get_job_details,
        "chat_toolbox": True,
        "data_visualization": True,
        "default_chart_type": "card",
    },
    {
        "name": "get_jobs_by_pm",
        "description": "Get all jobs for a specific Project Manager from ScheduleShare.",
        "category": "job_read",
        "display_category": "Jobs",
        "parameters": {
            "type": "object",
            "properties": {
                "pm_name": {
                    "type": "string",
                    "description": "The Project Manager's name (e.g. 'John Smith')"
                },
                "active_only": {
                    "type": "boolean",
                    "description": "Whether to return only active jobs (default true)"
                }
            },
            "required": ["pm_name"]
        },
        "executor": oa_get_jobs_by_pm,
        "chat_toolbox": True,
        "data_visualization": True,
        "default_chart_type": "line",
        "chart_config": {
            "x_axis": "JobNumber",
            "y_axis": "TotalHours",
            "x_axis_label": "Job",
            "y_axis_label": "Total Hours"
        }
    },
    {
        "name": "get_jobs_shipping_soon",
        "description": "Get jobs shipping within a specified number of days. Useful for tracking upcoming deadlines.",
        "category": "job_read",
        "display_category": "Jobs",
        "parameters": {
            "type": "object",
            "properties": {
                "days_ahead": {
                    "type": "integer",
                    "description": "Number of days to look ahead (default 30)"
                }
            },
            "required": []
        },
        "executor": oa_get_jobs_shipping_soon,
        "chat_toolbox": True,
        "data_visualization": True,
        "default_chart_type": "line",
        "chart_config": {
            "x_axis": "JobNumber",
            "y_axis": "DaysUntilShip",
            "x_axis_label": "Job Number",
            "y_axis_label": "Days Until Ship",
        },
    },
    
    # =========================================================================
    # Manager Reports (OT, Labor Costs, etc.)
    # =========================================================================
    {
        "name": "get_ot_hours_by_job",
        "description": "Get overtime hours for a specific job, broken down by employee. Shows who worked OT, total hours, and date ranges.",
        "category": "manager_reports",
        "display_category": "Overtime",
        "parameters": {
            "type": "object",
            "properties": {
                "job_number": {
                    "type": "string",
                    "description": "The job number to query (e.g. '6516')"
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format (defaults to 7 days ago)"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format (defaults to today)"
                }
            },
            "required": ["job_number"]
        },
        "executor": oa_get_ot_hours_by_job,
        "chat_toolbox": True,
        "data_visualization": True,
        "default_chart_type": "card",
        "chart_config": {
            "x_axis": "CLASTNAME",
            "y_axis": "TotalOTHours",
            "x_axis_label": "Employee",
            "y_axis_label": "OT Hours",
        },
    },
    {
        "name": "get_ot_hours_all_jobs",
        "description": "Get overtime hours summary across all jobs. Shows total OT per job, employee counts, and date ranges.",
        "category": "manager_reports",
        "display_category": "Overtime",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format (defaults to 7 days ago)"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format (defaults to today)"
                }
            },
            "required": []
        },
        "executor": oa_get_ot_hours_all_jobs,
        "chat_toolbox": True,
        "data_visualization": True,
        "default_chart_type": "bar",
        "chart_config": {
            "x_axis": "JobNumber",
            "y_axis": "TotalOTHours",
            "x_axis_label": "Job",
            "y_axis_label": "OT Hours",
        },
    },
    
    # =========================================================================
    # Memory Tools (AI-internal)
    # =========================================================================
    {
        "name": "search_user_memories",
        "description": "Search your memories about this user from past conversations. Use when the user references something from before, asks 'do you remember', or when historical context would help answer their question.",
        "category": "memory",
        "display_category": "Memory",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Keywords to search for in memories (e.g. 'project', 'preference', 'python')"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of memories to return (default 10)"
                }
            },
            "required": ["query"]
        },
        "executor": oa_search_user_memories,
        "chat_toolbox": False,  # AI-internal tool
        "data_visualization": False,
    },
    {
        "name": "save_user_memory",
        "description": "Save an important fact about the user to remember for future conversations. Use when you learn something significant like: their role, projects they're working on, preferences, skills, or important context. Be concise but specific.",
        "category": "memory",
        "display_category": "Memory",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The memory to save. Be concise but specific. (e.g. 'User is a data manager at MetalsFab', 'User prefers Python over C#')"
                },
                "memory_type": {
                    "type": "string",
                    "enum": ["fact", "preference", "project", "skill", "context"],
                    "description": "Type of memory: fact (personal info), preference (likes/dislikes), project (what they're working on), skill (expertise), context (other important info)"
                }
            },
            "required": ["content", "memory_type"]
        },
        "executor": oa_save_user_memory,
        "chat_toolbox": False,  # AI-internal tool
        "data_visualization": False,
    },
    
    # =========================================================================
    # Conversation Tools (AI-internal)
    # =========================================================================
    {
        "name": "search_conversations",
        "description": "Search past conversations by keyword. Searches titles, summaries, and message content. Returns ranked results with context snippets showing where matches occurred.",
        "category": "conversation",
        "display_category": "Conversations",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Keywords to search for (e.g., 'job 6516', 'CNC production', 'transmittal issues')"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results to return (default 10, max 20)"
                }
            },
            "required": ["query"]
        },
        "executor": oa_search_conversations,
        "chat_toolbox": False,  # AI-internal tool
        "data_visualization": False,
    },
    {
        "name": "get_recent_conversations",
        "description": "Get recent conversations by time window. Use for 'what did we discuss yesterday', 'conversations from last week', 'show me recent chats'.",
        "category": "conversation",
        "display_category": "Conversations",
        "parameters": {
            "type": "object",
            "properties": {
                "days_back": {
                    "type": "integer",
                    "description": "How many days to look back (default 7, max 90)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results to return (default 10, max 20)"
                }
            },
            "required": []
        },
        "executor": oa_get_recent_conversations,
        "chat_toolbox": False,  # AI-internal tool
        "data_visualization": False,
    },
    {
        "name": "get_conversation_messages",
        "description": "Fetch full message history for a specific conversation. Use AFTER search_conversations or get_recent_conversations when you need complete context beyond the summary.",
        "category": "conversation",
        "display_category": "Conversations",
        "parameters": {
            "type": "object",
            "properties": {
                "conversation_id": {
                    "type": "integer",
                    "description": "The conversation ID to retrieve messages for (obtained from search or recent conversations)"
                }
            },
            "required": ["conversation_id"]
        },
        "executor": oa_get_conversation_messages,
        "chat_toolbox": False,  # AI-internal tool
        "data_visualization": False,
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
    
    This is for the AI - it sees ALL permitted tools.
    
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


def get_chat_toolbox_tools(user_role: str) -> list[dict]:
    """
    Get tools for the chat sidebar UI toolbox.
    Filtered by permission AND chat_toolbox visibility flag.
    
    Only includes tools users should manually trigger (not AI-internal tools).
    
    Args:
        user_role: The user's role
        
    Returns:
        List of tools in simplified format for UI, with display_category for grouping
    """
    tools = []
    for tool in TOOL_REGISTRY:
        # Must be visible in chat toolbox (default True)
        if not tool.get("chat_toolbox", True):
            continue
        # Must have permission
        if not can_use_tool(user_role, tool["category"]):
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


def get_data_tools(user_role: str) -> list[dict]:
    """
    Get tools available for data visualization page.
    Only includes tools with data_visualization=True, filtered by permission.
    
    Args:
        user_role: The user's role
        
    Returns:
        List of tools in simplified format for data page, with display_category for grouping
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
