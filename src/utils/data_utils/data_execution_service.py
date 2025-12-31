"""
Orchestrates tool execution, normalization, and result storage.

This is the central service that ties together:
- MCP tool execution
- Result normalization
- Database storage
- Status management
"""
from typing import Any
from src.utils.data_utils.data_session_service import DataSessionService
from src.utils.data_utils.data_result_service import DataResultService
from src.utils.data_utils.tool_normalizer import ToolNormalizer
from src.utils.data_utils.data_session import DataSession
from src.utils.data_utils.data_result import DataResult, NormalizedResult

# Import tool executors
from src.tools.local_mcp_tools.local_mcp_tool_getAllJobInfo import oa_get_jobs
from src.tools.local_mcp_tools.local_mcp_tool_getJobInfo import oa_get_job_info


class DataExecutionService:
    """
    Executes MCP tools and stores normalized results.
    
    Usage:
        service = DataExecutionService()
        session, result = service.execute(session_id)
    """
    
    def __init__(self):
        self.normalizer = ToolNormalizer()
        
        # Map tool names to their executor functions
        self._tool_executors = {
            "get_all_job_info": self._execute_get_all_jobs,
            "get_job_info": self._execute_get_job_info,
        }

    def execute(self, session_id: int) -> tuple[DataSession, DataResult | None]:
        """
        Executes the tool for a session and stores the result.
        
        Flow:
        1. Set status to 'running'
        2. Execute the tool
        3. Normalize the result
        4. Store the result
        5. Set status to 'success' or 'error'
        
        Args:
            session_id: The session to execute
            
        Returns:
            Tuple of (updated session, result or None if error)
        """
        # Get session
        session = DataSessionService.get_session(session_id)
        if session is None:
            raise ValueError(f"Session {session_id} not found")
        
        # Update status to running
        DataSessionService.set_status(session_id, "running")
        
        try:
            # Execute the tool
            raw_result = self._execute_tool(session.tool_name, session.tool_params)
            
            # Normalize the result
            normalized = self.normalizer.normalize(session.tool_name, raw_result)
            
            # Store the result
            result = DataResultService.create_result(session_id, normalized)
            
            # Update status to success
            DataSessionService.set_status(session_id, "success")
            
            # Return updated session and result
            updated_session = DataSessionService.get_session(session_id)
            return updated_session, result
            
        except Exception as e:
            # Update status to error
            error_message = f"{type(e).__name__}: {str(e)}"
            DataSessionService.set_status(session_id, "error", error_message)
            
            # Return updated session (with error), no result
            updated_session = DataSessionService.get_session(session_id)
            return updated_session, None

    def execute_preview(self, tool_name: str, tool_params: dict = None) -> NormalizedResult:
        """
        Executes a tool and returns normalized result without storing.
        Useful for previewing what a tool will return.
        
        Args:
            tool_name: The tool to execute
            tool_params: Tool parameters
            
        Returns:
            NormalizedResult (not persisted)
        """
        raw_result = self._execute_tool(tool_name, tool_params)
        return self.normalizer.normalize(tool_name, raw_result)

    def _execute_tool(self, tool_name: str, tool_params: dict = None) -> Any:
        """
        Routes to the appropriate tool executor.
        
        Args:
            tool_name: The tool identifier
            tool_params: Parameters for the tool
            
        Returns:
            Raw tool output
        """
        executor = self._tool_executors.get(tool_name)
        
        if executor is None:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        return executor(tool_params)

    def _execute_get_all_jobs(self, params: dict = None) -> Any:
        """Execute get_all_job_info tool."""
        return oa_get_jobs()

    def _execute_get_job_info(self, params: dict = None) -> Any:
        """Execute get_job_info tool."""
        if not params or "job_number" not in params:
            raise ValueError("job_number parameter is required for get_job_info")
        
        return oa_get_job_info(params["job_number"])

    def get_available_tools(self) -> list[dict]:
        """
        Returns list of tools available for data visualization.
        
        Returns:
            List of tool definitions with name, description, parameters
        """
        return [
            {
                "name": "get_all_job_info",
                "description": "Get a list of all jobs with basic info",
                "parameters": []
            },
            {
                "name": "get_job_info", 
                "description": "Get detailed information about a specific job",
                "parameters": [
                    {
                        "name": "job_number",
                        "type": "string",
                        "required": True,
                        "description": "The job number to retrieve"
                    }
                ]
            }
        ]
