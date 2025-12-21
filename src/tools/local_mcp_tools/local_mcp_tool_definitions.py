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
    }
]