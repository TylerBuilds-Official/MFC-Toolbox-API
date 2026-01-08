TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_job_info",
            "description": "Get detailed information about a specific job by job number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_number": {
                        "type": "string",
                        "description": "The job number to retrieve information for. (e.g. 6516)"
                    }
                },
                "required": ["job_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_job_info",
            "description": "Get a list of all jobs with basic info (job number, name, contractor, location, etc.)",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_machine_production",
            "description": "Get daily production counts per CNC machine (pieces processed and total weight) over a date range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days_back": {
                        "type": "integer",
                        "description": "Number of days to look back (default 30)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_user_memories",
            "description": "Search your memories about this user from past conversations. Use when the user references something from before, asks 'do you remember', or when historical context would help answer their question.",
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
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_user_memory",
            "description": "Save an important fact about the user to remember for future conversations. Use when you learn something significant like: their role, projects they're working on, preferences, skills, or important context. Be concise but specific.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The memory to save. Be concise but specific. (e.g. 'User is a data manager at MetalsFab', 'User prefers Python over C#', 'User is building MFC Toolbox app')"
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
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_user_memory",
            "description": "Update an existing memory's content or type. Use when information changes (user changed roles, project completed, preference updated). Requires the memory_id from search results.",
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
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_user_memory",
            "description": "Delete a memory that is no longer relevant. Use when information is outdated, was saved incorrectly, or user explicitly asks to forget something.",
            "parameters": {
                "type": "object",
                "properties": {
                    "memory_id": {
                        "type": "integer",
                        "description": "The ID of the memory to delete (from search_user_memories results)"
                    }
                },
                "required": ["memory_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_user_memories",
            "description": "Get all memories about this user. Use when asked 'what do you know about me?' or when you need a complete picture of stored information. Can filter by memory type.",
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
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_conversations",
            "description": "Search past conversations by keyword. Searches titles, summaries, and message content. Returns ranked results with context snippets showing where matches occurred. Use when user references past discussions, asks 'did we talk about...', 'what did we discuss regarding...', or when historical conversation context would help. Returns max 10 results by default - refine search terms or increase limit if more results needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Keywords to search for (e.g., 'job 6516', 'CNC production', 'transmittal issues', 'drawing review')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results to return (default 10, max 20)"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_conversations",
            "description": "Get recent conversations by time window. Use for 'what did we discuss yesterday', 'conversations from last week', 'show me recent chats', or 'continue where we left off'. Returns conversations sorted by most recent activity. Useful for time-based queries rather than keyword searches.",
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
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_conversation_messages",
            "description": "Fetch full message history for a specific conversation. Use AFTER search_conversations or get_recent_conversations when you need complete context beyond the summary. Returns all messages in chronological order including any extended thinking content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "conversation_id": {
                        "type": "integer",
                        "description": "The conversation ID to retrieve messages for (obtained from search or recent conversations)"
                    }
                },
                "required": ["conversation_id"]
            }
        }
    }
]
