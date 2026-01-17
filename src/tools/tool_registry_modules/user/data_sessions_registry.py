"""
Data Sessions Tools Registry - User Level

Accessible by: user, manager, admin
Category: data_sessions
Display Category: Data Sessions

AI-internal tools for searching and retrieving past data queries.
Allows the AI to reference previous reports and data analysis sessions.
"""

from src.tools.local_mcp_tools.local_mcp_tool_searchDataSessions import oa_search_data_sessions
from src.tools.local_mcp_tools.local_mcp_tool_getDataSessions import oa_get_data_sessions
from src.tools.local_mcp_tools.local_mcp_tool_getDataSessionDetails import oa_get_data_session_details


DATA_SESSION_TOOLS = [
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
]
