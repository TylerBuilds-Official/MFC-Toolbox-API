"""
Centralized Tool Registry

Single source of truth for all tools available in the system.
Contains:
- Tool definitions (name, description, parameters)
- Permission categories (category → role-based access)
- Display categories (display_category → UI grouping)
- Execution references (executor function)
- Context injection flags (needs_user_id, needs_conversation_id, is_async)
- Visibility flags (chat_toolbox, data_visualization)

All helper functions are in tool_utils.py
"""

# =============================================================================
# Role Hierarchy
# =============================================================================
# Higher number = more permissions
# A role can access anything at or below its level

ROLE_HIERARCHY = {
    "pending": 0,           # Newly registered, awaiting approval
    "user": 10,             # Standard user
    "manager": 100,         # Elevated access for supervisors/managers
#   "new_role_one": 200,    # Example new role
    "admin": 500,           # Full access
}


# =============================================================================
# Tool Categories
# =============================================================================
# Maps category name to minimum role required

TOOL_CATEGORIES = {
    "job_read": "user",             # View job data
    "job_write": "admin",           # Modify job data (future)
    "reports": "user",              # Run reports
    "manager_reports": "manager",   # Sensitive reports (OT, labor costs, etc.)
    "admin_tools": "admin",         # System administration
    "memory": "user",               # Memory tools (search/save memories)
    "conversation": "user",         # Conversation tools (search/retrieve past conversations)
    "data_sessions": "user",        # Data session tools (search/retrieve past data sessions)
    "artifacts": "user",            # Artifact creation tools
    "company_info": "user",         # Company/employee lookups
    "filesystem": "user",           # Filesystem operations (via agent connector)
}


# =============================================================================
# Executor Imports
# =============================================================================
# Import all executor functions

# Job Tools
from src.tools.local_mcp_tools.local_mcp_tool_getAllJobInfo import oa_get_jobs
from src.tools.local_mcp_tools.local_mcp_tool_getJobInfo import oa_get_job_info
from src.tools.local_mcp_tools.local_mcp_tool_getMachineProductionData import oa_get_machine_production
from src.tools.local_mcp_tools.local_mcp_tool_getOTHoursByJob import oa_get_ot_hours_by_job
from src.tools.local_mcp_tools.local_mcp_tool_getOTHoursAllJobs import oa_get_ot_hours_all_jobs
from src.tools.local_mcp_tools.local_mcp_tool_getActiveJobs import oa_get_active_jobs
from src.tools.local_mcp_tools.local_mcp_tool_getJobsByPM import oa_get_jobs_by_pm
from src.tools.local_mcp_tools.local_mcp_tool_getJobsShippingSoon import oa_get_jobs_shipping_soon

# Memory Tools
from src.tools.local_mcp_tools.local_mcp_tool_searchUserMemories import oa_search_user_memories
from src.tools.local_mcp_tools.local_mcp_tool_saveUserMemory import oa_save_user_memory
from src.tools.local_mcp_tools.local_mcp_tool_updateUserMemory import oa_update_user_memory
from src.tools.local_mcp_tools.local_mcp_tool_deleteUserMemory import oa_delete_user_memory
from src.tools.local_mcp_tools.local_mcp_tool_getAllUserMemories import oa_get_all_user_memories

# Conversation Tools
from src.tools.local_mcp_tools.local_mcp_tool_searchConversations import oa_search_conversations
from src.tools.local_mcp_tools.local_mcp_tool_getRecentConversations import oa_get_recent_conversations
from src.tools.local_mcp_tools.local_mcp_tool_getConversationMessages import oa_get_conversation_messages

# Data Session Tools
from src.tools.local_mcp_tools.local_mcp_tool_searchDataSessions import oa_search_data_sessions
from src.tools.local_mcp_tools.local_mcp_tool_getDataSessions import oa_get_data_sessions
from src.tools.local_mcp_tools.local_mcp_tool_getDataSessionDetails import oa_get_data_session_details

# Artifact Tools
from src.tools.local_mcp_tools.local_mcp_tool_createDataArtifact import oa_create_data_artifact

# Company Data Tools
from src.tools.local_mcp_tools.company_data import (
    oa_get_employee,
    oa_get_employee_email,
    oa_get_employee_phone,
    oa_get_employees_by_department,
    oa_get_project_managers,
    oa_get_it_team,
    oa_search_employees,
    oa_get_employee_directory_summary,
    oa_get_department_summary,
    oa_list_departments,
    oa_get_company_info,
    oa_get_contact_info,
    oa_get_all_company_data,
)

# Filesystem Tools (Agent Connector)
from src.tools.local_mcp_tools.filesystem_tools import (
    # Directory operations
    oa_fs_list_directory,
    oa_fs_create_directory,
    oa_fs_directory_tree,
    # File operations
    oa_fs_read_file,
    oa_fs_write_file,
    oa_fs_edit_file,
    oa_fs_delete_file,
    oa_fs_copy_file,
    oa_fs_move_file,
    # Search & info
    oa_fs_search_files,
    oa_fs_get_file_info,
    oa_fs_file_exists,
    # Non-async
    oa_fs_get_allowed_folders,
)


# =============================================================================
# Tool Registry
# =============================================================================

TOOL_REGISTRY: list[dict] = [
    # =========================================================================
    # Job Tools
    # =========================================================================
    {
        "name": "get_all_job_info",
        "description": "Get a list of all jobs with basic info (job number, name, contractor, location, etc.)",
        "category": "job_read",
        "display_category": "Jobs",

        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },

        "executor": oa_get_jobs,
        "chat_toolbox": True,
        "data_visualization": True,
        "default_chart_type": "table",
        "normalizer": "job_list",
    },


    {
        "name": "get_job_info",
        "description": "Get comprehensive job information including hours, dates, financials, production data (pieces/weight), and status. Merges data from Tekla and ScheduleShare.",
        "category": "job_read",
        "display_category": "Jobs",

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

        "executor": oa_get_job_info,
        "chat_toolbox": True,
        "data_visualization": True,
        "default_chart_type": "card",
    },


    {
        "name": "get_machine_production",
        "description": "Get daily production counts per CNC machine (pieces processed and total weight) over a date range.",
        "category": "reports",
        "display_category": "Production",

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

        "executor": oa_get_machine_production,
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

        "normalizer": None,
    },


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
    # Memory Tools (AI-internal, need user_id)
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
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
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
                },
                "expires_in_days": {
                    "type": "integer",
                    "description": "Optional: auto-expire this memory after N days. Use for temporary context like active projects (30-90 days) or time-sensitive info. Omit for permanent facts."
                }
            },
            "required": ["content", "memory_type"]
        },

        "executor": oa_save_user_memory,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        "needs_conversation_id": True,
    },


    {
        "name": "update_user_memory",
        "description": "Update an existing memory's content or type. Use when information changes (user changed roles, project completed, preference updated). Requires the memory_id from search results.",
        "category": "memory",
        "display_category": "Memory",

        "parameters": {
            "type": "object",
            "properties": {
                "memory_id": {
                    "type": "integer",
                    "description": "The ID of the memory to update (from search_user_memories results)"
                },
                "content": {
                    "type": "string",
                    "description": "New content for the memory (optional)"
                },
                "memory_type": {
                    "type": "string",
                    "enum": ["fact", "preference", "project", "skill", "context"],
                    "description": "New type for the memory (optional)"
                }
            },
            "required": ["memory_id"]
        },

        "executor": oa_update_user_memory,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
    },


    {
        "name": "delete_user_memory",
        "description": "Delete a memory that is no longer relevant. Use when information is outdated, was saved incorrectly, or user explicitly asks to forget something.",
        "category": "memory",
        "display_category": "Memory",

        "parameters": {
            "type": "object",
            "properties": {
                "memory_id": {
                    "type": "integer",
                    "description": "The ID of the memory to delete (from search_user_memories results)"
                }
            },
            "required": ["memory_id"]
        },

        "executor": oa_delete_user_memory,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
    },


    {
        "name": "get_all_user_memories",
        "description": "Get all memories about this user. Use when asked 'what do you know about me?' or when you need a complete picture of stored information. Can filter by memory type.",
        "category": "memory",
        "display_category": "Memory",

        "parameters": {
            "type": "object",
            "properties": {
                "memory_type": {
                    "type": "string",
                    "enum": ["fact", "preference", "project", "skill", "context"],
                    "description": "Filter by type (optional)"
                }
            },
            "required": []
        },

        "executor": oa_get_all_user_memories,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
    },

    
    # =========================================================================
    # Conversation Tools (AI-internal, need user_id)
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
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
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
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
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
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
    },

    
    # =========================================================================
    # Data Session Tools (AI-internal, need user_id)
    # =========================================================================
    {
        "name": "search_data_sessions",
        "description": "Search the user's data sessions by keyword. Searches titles, AI summaries, tool names, and parameters. Use when the user references past data queries, asks about reports they ran, or when you need to find previous data analysis. Returns ranked results with relevance scores.",
        "category": "data_sessions",
        "display_category": "Data Sessions",

        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Keywords to search for (e.g., 'production', 'job 6516', 'overtime', 'machine')"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results to return (default 15, max 50)"
                }
            },
            "required": ["query"]
        },

        "executor": oa_search_data_sessions,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
    },


    {
        "name": "get_data_sessions",
        "description": "Get data sessions with flexible filtering and sorting. Use for 'show my recent data', 'what reports did I run last week', 'my first data sessions'. Supports date ranges, tool filters, and ascending/descending order.",
        "category": "data_sessions",
        "display_category": "Data Sessions",

        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum sessions to return (default 10, max 50)"
                },
                "sort_by": {
                    "type": "string",
                    "enum": ["created_at", "updated_at"],
                    "description": "Sort field (default 'updated_at')"
                },
                "sort_order": {
                    "type": "string",
                    "enum": ["asc", "desc"],
                    "description": "Sort direction - 'asc' for oldest first, 'desc' for newest first (default 'desc')"
                },
                "tool_name": {
                    "type": "string",
                    "description": "Filter by specific tool (e.g., 'get_machine_production', 'get_ot_hours_by_job')"
                },
                "status": {
                    "type": "string",
                    "enum": ["pending", "running", "success", "error"],
                    "description": "Filter by status"
                },
                "after_date": {
                    "type": "string",
                    "description": "ISO date - only sessions after this date (e.g., '2025-01-01T00:00:00')"
                },
                "before_date": {
                    "type": "string",
                    "description": "ISO date - only sessions before this date"
                }
            },
            "required": []
        },

        "executor": oa_get_data_sessions,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
    },

    {
        "name": "get_data_session_details",
        "description": "Get full details for a specific data session including result preview. Use AFTER search_data_sessions or get_data_sessions when you need: the exact parameters used, actual data to summarize, or parent session info for lineage. Returns session metadata and preview of result rows.",
        "category": "data_sessions",
        "display_category": "Data Sessions",

        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "integer",
                    "description": "The session ID to retrieve (obtained from search or get_data_sessions)"
                },
                "max_preview_rows": {
                    "type": "integer",
                    "description": "Number of result rows to include in preview (default 10, max 50)"
                }
            },
            "required": ["session_id"]
        },

        "executor": oa_get_data_session_details,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
    },

    
    # =========================================================================
    # Artifact Tools (AI-internal, need user_id and conversation_id)
    # =========================================================================
    {
        "name": "create_data_artifact",
        "description": "Create a clickable data visualization card in the chat response. Use this when the user asks for data that would benefit from interactive visualization - job info, production reports, overtime summaries, etc. The artifact appears as a card the user can click to open a full data visualization page. Use parent_session_id when re-running or refining a previous query to maintain lineage.",
        "category": "artifacts",
        "display_category": "Artifacts",

        "parameters": {
            "type": "object",
            "properties": {
                "target_tool": {
                    "type": "string",
                    "description": "The data tool to use (e.g., 'get_job_info', 'get_machine_production', 'get_ot_hours_by_job')"
                },
                "tool_params": {
                    "type": "object",
                    "description": "A flat dict mapping parameter names to values. Example: {'job_number': '6516'} or {'days_back': 30}. Do NOT use nested key/value structures."
                },
                "chart_type": {
                    "type": "string",
                    "enum": ["bar", "line", "pie", "table", "card"],
                    "description": "Suggested visualization type (optional - uses tool default if not specified)"
                },
                "title": {
                    "type": "string",
                    "description": "Custom title for the artifact card (optional - auto-generated if not provided)"
                },
                "parent_session_id": {
                    "type": "integer",
                    "description": "Optional parent session ID for lineage tracking. Use when re-running or refining a previous query to link the new session to its parent."
                }
            },
            "required": ["target_tool"]
        },

        "executor": oa_create_data_artifact,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        "needs_conversation_id": True,
    },

    
    # =========================================================================
    # Company Data Tools (AI-internal)
    # =========================================================================
    {
        "name": "get_employee",
        "description": "Look up a specific employee's contact info by name. Supports fuzzy matching (e.g., 'blake', 'Blake Reed', 'blak' all work). Returns position, email, extension, and cell. Use for 'what's [name]'s email/phone/extension?'",
        "category": "company_info",
        "display_category": "Company",

        "parameters": {
            "type": "object",
            "properties": {
                "employee_name": {
                    "type": "string",
                    "description": "Full or partial employee name (e.g., 'blake', 'Blake Reed')"
                }
            },
            "required": ["employee_name"]
        },

        "executor": oa_get_employee,
        "chat_toolbox": False,
        "data_visualization": False,
    },


    {
        "name": "get_employee_email",
        "description": "Quick email lookup for a specific employee. Supports fuzzy name matching. Use when user just needs an email address.",
        "category": "company_info",
        "display_category": "Company",

        "parameters": {
            "type": "object",
            "properties": {
                "employee_name": {
                    "type": "string",
                    "description": "Full or partial employee name"
                }
            },
            "required": ["employee_name"]
        },

        "executor": oa_get_employee_email,
        "chat_toolbox": False,
        "data_visualization": False,
    },


    {
        "name": "get_employee_phone",
        "description": "Get phone contact info (extension and cell) for a specific employee. Supports fuzzy name matching.",
        "category": "company_info",
        "display_category": "Company",

        "parameters": {
            "type": "object",
            "properties": {
                "employee_name": {
                    "type": "string",
                    "description": "Full or partial employee name"
                }
            },
            "required": ["employee_name"]
        },

        "executor": oa_get_employee_phone,
        "chat_toolbox": False,
        "data_visualization": False,
    },


    {
        "name": "get_employees_by_department",
        "description": "List all employees in a department. Valid departments: executive, it, purchasing, project_mgmt, estimating, admin, safety, sales. Also accepts aliases like 'pm', 'tech', 'dev', 'office', 'leadership', 'exec'.",
        "category": "company_info",
        "display_category": "Company",

        "parameters": {
            "type": "object",
            "properties": {
                "department": {
                    "type": "string",
                    "description": "Department name or alias (e.g., 'it', 'project_mgmt', 'pm', 'exec')"
                }
            },
            "required": ["department"]
        },

        "executor": oa_get_employees_by_department,
        "chat_toolbox": False,
        "data_visualization": False,
    },


    {
        "name": "get_project_managers",
        "description": "Get all project managers. Shortcut for common query - returns list of PMs with contact info.",
        "category": "company_info",
        "display_category": "Company",

        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },

        "executor": oa_get_project_managers,
        "chat_toolbox": False,
        "data_visualization": False,
    },


    {
        "name": "get_it_team",
        "description": "Get all IT/Development team members. Returns list with contact info.",
        "category": "company_info",
        "display_category": "Company",

        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },

        "executor": oa_get_it_team,
        "chat_toolbox": False,
        "data_visualization": False,
    },


    {
        "name": "search_employees",
        "description": "Search employees by name, position, or email. Use as fallback when get_employee returns nothing, or for role-based queries like 'who handles purchasing' or 'find estimators'.",
        "category": "company_info",
        "display_category": "Company",

        "parameters": {
            "type": "object",
            "properties": {
                "search_term": {
                    "type": "string",
                    "description": "Search term to match against name, position, or email"
                }
            },
            "required": ["search_term"]
        },

        "executor": oa_search_employees,
        "chat_toolbox": False,
        "data_visualization": False,
    },


    {
        "name": "get_employee_directory_summary",
        "description": "Get a compact, scannable employee directory. Returns all employees with position and extension, one per line. Low token cost overview.",
        "category": "company_info",
        "display_category": "Company",

        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },

        "executor": oa_get_employee_directory_summary,
        "chat_toolbox": False,
        "data_visualization": False,
    },


    {
        "name": "get_department_summary",
        "description": "Get a summary of all departments and their members. Shows org structure at a glance.",
        "category": "company_info",
        "display_category": "Company",

        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },

        "executor": oa_get_department_summary,
        "chat_toolbox": False,
        "data_visualization": False,
    },


    {
        "name": "list_departments",
        "description": "Get list of valid department names. Use for disambiguation or when unsure which department to query.",
        "category": "company_info",
        "display_category": "Company",

        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },

        "executor": oa_list_departments,
        "chat_toolbox": False,
        "data_visualization": False,
    },


    {
        "name": "get_company_info",
        "description": "Get company information for MFC or Master Machining. Returns address, phone, fax, website, and description. Use 'mfc' (default) or 'mmm'/'master machining' for entity parameter.",
        "category": "company_info",
        "display_category": "Company",

        "parameters": {
            "type": "object",
            "properties": {
                "entity": {
                    "type": "string",
                    "description": "Which company: 'mfc' (default) or 'mmm' for Master Machining"
                }
            },
            "required": []
        },

        "executor": oa_get_company_info,
        "chat_toolbox": False,
        "data_visualization": False,
    },


    {
        "name": "get_contact_info",
        "description": "Get MFC office address, phone, fax, and website. Use for 'where is the office', 'company phone number', 'MFC address', directions questions.",
        "category": "company_info",
        "display_category": "Company",

        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },

        "executor": oa_get_contact_info,
        "chat_toolbox": False,
        "data_visualization": False,
    },


    {
        "name": "get_all_company_data",
        "description": "Get complete company data dump including all employees and business info. Use sparingly - prefer targeted tools for most queries. High token cost.",
        "category": "company_info",
        "display_category": "Company",

        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },

        "executor": oa_get_all_company_data,
        "chat_toolbox": False,
        "data_visualization": False,
    },

    
    # =========================================================================
    # Filesystem Tools (Agent Connector - async, need user_id)
    # =========================================================================
    {
        "name": "fs_list_directory",
        "description": "List contents of a directory on the user's computer. Returns files and folders with metadata. Requires the user to have the Filesystem Connector enabled and the path to be in their allowed folders. Use fs_get_allowed_folders first to see what paths are accessible.",
        "category": "filesystem",
        "display_category": "Filesystem",

        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to list (e.g., 'C:\\Projects' or 'D:\\Data')"
                }
            },
            "required": ["path"]
        },

        "executor": oa_fs_list_directory,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        "is_async": True,
    },


    {
        "name": "fs_read_file",
        "description": "Read the contents of a text file on the user's computer. Returns the file content as text. Use for reading code files, config files, logs, text documents, etc. Requires read permission on the containing folder.",
        "category": "filesystem",
        "display_category": "Filesystem",

        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Full path to the file to read (e.g., 'C:\\Projects\\app\\config.json')"
                }
            },
            "required": ["path"]
        },

        "executor": oa_fs_read_file,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        "is_async": True,
    },


    {
        "name": "fs_write_file",
        "description": "Write content to a file on the user's computer. Creates the file if it doesn't exist, overwrites if it does. Use for creating/updating code files, configs, scripts, etc. Requires write permission on the containing folder.",
        "category": "filesystem",
        "display_category": "Filesystem",

        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Full path to the file to write (e.g., 'C:\\Projects\\output.txt')"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                }
            },
            "required": ["path", "content"]
        },

        "executor": oa_fs_write_file,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        "is_async": True,
    },


    {
        "name": "fs_delete_file",
        "description": "Delete a file on the user's computer. This is permanent and cannot be undone. Requires delete permission on the containing folder. Use with caution.",
        "category": "filesystem",
        "display_category": "Filesystem",

        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Full path to the file to delete"
                }
            },
            "required": ["path"]
        },

        "executor": oa_fs_delete_file,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        "is_async": True,
    },


    {
        "name": "fs_get_allowed_folders",
        "description": "Get the list of folders the user has allowed access to via the Filesystem Connector. Shows which paths you can read/write/delete. Call this first before attempting file operations to understand what's accessible.",
        "category": "filesystem",
        "display_category": "Filesystem",

        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },

        "executor": oa_fs_get_allowed_folders,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        # Note: fs_get_allowed_folders is NOT async - doesn't need agent.
    },


    {
        "name": "fs_create_directory",
        "description": "Create a directory on the user's computer. Creates parent directories automatically if needed. Requires write permission on the parent folder.",
        "category": "filesystem",
        "display_category": "Filesystem",

        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to create (e.g., 'C:\\Projects\\NewFolder')"
                },
                "parents": {
                    "type": "boolean",
                    "description": "Create parent directories if they don't exist (default true)"
                }
            },
            "required": ["path"]
        },

        "executor": oa_fs_create_directory,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        "is_async": True,
    },


    {
        "name": "fs_directory_tree",
        "description": "Get a recursive tree view of a directory on the user's computer. Returns nested structure with files and folders. Useful for understanding project structure. Use max_depth to limit recursion for large directories.",
        "category": "filesystem",
        "display_category": "Filesystem",

        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Root directory path to scan"
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum recursion depth (default 5, max 10)"
                },
                "include_files": {
                    "type": "boolean",
                    "description": "Include files in output, not just directories (default true)"
                },
                "include_hidden": {
                    "type": "boolean",
                    "description": "Include hidden files and folders (default false)"
                }
            },
            "required": ["path"]
        },

        "executor": oa_fs_directory_tree,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        "is_async": True,
    },


    {
        "name": "fs_edit_file",
        "description": "Edit a file by finding and replacing text. The old_text must appear exactly once in the file (for safe, unambiguous replacement). Use for targeted code edits, config changes, etc. If text appears multiple times, add more surrounding context to make it unique.",
        "category": "filesystem",
        "display_category": "Filesystem",

        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Full path to the file to edit"
                },
                "old_text": {
                    "type": "string",
                    "description": "Text to find and replace (must appear exactly once in file)"
                },
                "new_text": {
                    "type": "string",
                    "description": "Replacement text (can be empty to delete the old_text)"
                }
            },
            "required": ["path", "old_text", "new_text"]
        },

        "executor": oa_fs_edit_file,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        "is_async": True,
    },


    {
        "name": "fs_copy_file",
        "description": "Copy a file to a new location on the user's computer. If destination is a directory, the file is copied into it with the same name. Creates parent directories if needed. Requires read permission on source and write permission on destination.",
        "category": "filesystem",
        "display_category": "Filesystem",

        "parameters": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Source file path to copy from"
                },
                "destination": {
                    "type": "string",
                    "description": "Destination path (file or directory)"
                }
            },
            "required": ["source", "destination"]
        },

        "executor": oa_fs_copy_file,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        "is_async": True,
    },


    {
        "name": "fs_move_file",
        "description": "Move or rename a file or directory on the user's computer. Works for both files and directories. If destination is an existing directory, the source is moved into it. Requires delete permission on source and write permission on destination.",
        "category": "filesystem",
        "display_category": "Filesystem",

        "parameters": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Source path (file or directory) to move"
                },
                "destination": {
                    "type": "string",
                    "description": "Destination path"
                }
            },
            "required": ["source", "destination"]
        },

        "executor": oa_fs_move_file,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        "is_async": True,
    },


    {
        "name": "fs_search_files",
        "description": "Search for files matching a pattern on the user's computer. Supports glob patterns (*.py, **/*.txt) or simple substring matching. Searches recursively from the given path. Use for finding files when you don't know the exact location.",
        "category": "filesystem",
        "display_category": "Filesystem",

        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory to search in"
                },
                "pattern": {
                    "type": "string",
                    "description": "Search pattern - glob (*.py, *.txt) or substring to match in filename"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum results to return (default 100, max 500)"
                },
                "include_hidden": {
                    "type": "boolean",
                    "description": "Include hidden files in results (default false)"
                }
            },
            "required": ["path", "pattern"]
        },

        "executor": oa_fs_search_files,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        "is_async": True,
    },


    {
        "name": "fs_get_file_info",
        "description": "Get detailed metadata about a file or directory on the user's computer. Returns name, size, type (file/directory), and timestamps (created, modified, accessed). Use to check file details before operations.",
        "category": "filesystem",
        "display_category": "Filesystem",

        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to file or directory"
                }
            },
            "required": ["path"]
        },

        "executor": oa_fs_get_file_info,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        "is_async": True,
    },


    {
        "name": "fs_file_exists",
        "description": "Check if a file or directory exists on the user's computer. Returns existence status and whether it's a file or directory. Quick check before attempting operations.",
        "category": "filesystem",
        "display_category": "Filesystem",

        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to check"
                }
            },
            "required": ["path"]
        },

        "executor": oa_fs_file_exists,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        "is_async": True,
    },


]
