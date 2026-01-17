"""
Conversation Tools Registry - User Level

Accessible by: user, manager, admin
Category: conversation
Display Category: Conversations

AI-internal tools for searching and retrieving past conversations.
Allows the AI to reference previous discussions for context continuity.
"""

from src.tools.local_mcp_tools.local_mcp_tool_searchConversations import oa_search_conversations
from src.tools.local_mcp_tools.local_mcp_tool_getRecentConversations import oa_get_recent_conversations
from src.tools.local_mcp_tools.local_mcp_tool_getConversationMessages import oa_get_conversation_messages


CONVERSATION_TOOLS = [
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
]
