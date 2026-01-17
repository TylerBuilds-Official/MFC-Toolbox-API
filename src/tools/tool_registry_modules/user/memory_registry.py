"""
Memory Tools Registry - User Level

Accessible by: user, manager, admin
Category: memory
Display Category: Memory

AI-internal tools for managing user memories across conversations.
These tools allow the AI to remember facts, preferences, and context about users.
"""

from src.tools.local_mcp_tools.local_mcp_tool_searchUserMemories import oa_search_user_memories
from src.tools.local_mcp_tools.local_mcp_tool_saveUserMemory import oa_save_user_memory
from src.tools.local_mcp_tools.local_mcp_tool_updateUserMemory import oa_update_user_memory
from src.tools.local_mcp_tools.local_mcp_tool_deleteUserMemory import oa_delete_user_memory
from src.tools.local_mcp_tools.local_mcp_tool_getAllUserMemories import oa_get_all_user_memories


MEMORY_TOOLS = [
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
]
