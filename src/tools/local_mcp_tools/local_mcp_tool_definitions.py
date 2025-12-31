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
                    }
                },
                "required": ["content", "memory_type"]
            }
        }
    }
]
