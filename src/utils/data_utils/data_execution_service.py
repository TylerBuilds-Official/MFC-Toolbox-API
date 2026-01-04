"""
Orchestrates tool execution, normalization, and result storage.

This is the central service that ties together:
- Tool registry (single source of truth)
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

# Import from centralized registry
from src.tools.tool_registry import (
    get_tool,
    get_executor,
    get_data_tools,
    can_use_tool,
)


class DataExecutionService:
    """
    Executes tools and stores normalized results.
    
    Usage:
        service = DataExecutionService()
        session, result = service.execute(session_id, user_role)
    """
    
    def __init__(self):
        self.normalizer = ToolNormalizer()

    def execute(
        self, 
        session_id: int, 
        user_role: str = "user"
    ) -> tuple[DataSession, DataResult | None]:
        """
        Executes the tool for a session and stores the result.
        
        Flow:
        1. Verify user has permission for this tool
        2. Set status to 'running'
        3. Execute the tool
        4. Normalize the result
        5. Store the result
        6. Set status to 'success' or 'error'
        
        Args:
            session_id: The session to execute
            user_role: The user's role for permission checking
            
        Returns:
            Tuple of (updated session, result or None if error)
            
        Raises:
            ValueError: If session not found or tool unknown
            PermissionError: If user lacks permission for tool
        """
        # Get session
        session = DataSessionService.get_session(session_id)
        if session is None:
            raise ValueError(f"Session {session_id} not found")
        
        # Get tool definition
        tool = get_tool(session.tool_name)
        if tool is None:
            raise ValueError(f"Unknown tool: {session.tool_name}")
        
        # Check permissions
        if not can_use_tool(user_role, tool["category"]):
            raise PermissionError(
                f"Role '{user_role}' does not have permission to use tool '{session.tool_name}'"
            )
        
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

    def execute_preview(
        self, 
        tool_name: str, 
        tool_params: dict = None,
        user_role: str = "user"
    ) -> NormalizedResult:
        """
        Executes a tool and returns normalized result without storing.
        Useful for previewing what a tool will return.
        
        Args:
            tool_name: The tool to execute
            tool_params: Tool parameters
            user_role: The user's role for permission checking
            
        Returns:
            NormalizedResult (not persisted)
            
        Raises:
            PermissionError: If user lacks permission
        """
        # Get tool and check permissions
        tool = get_tool(tool_name)
        if tool is None:
            raise ValueError(f"Unknown tool: {tool_name}")
            
        if not can_use_tool(user_role, tool["category"]):
            raise PermissionError(
                f"Role '{user_role}' does not have permission to use tool '{tool_name}'"
            )
        
        raw_result = self._execute_tool(tool_name, tool_params)
        return self.normalizer.normalize(tool_name, raw_result)

    def _execute_tool(self, tool_name: str, tool_params: dict = None) -> Any:
        """
        Executes a tool by name using the registry.
        
        Args:
            tool_name: The tool identifier
            tool_params: Parameters for the tool
            
        Returns:
            Raw tool output
        """
        executor = get_executor(tool_name)
        
        if executor is None:
            raise ValueError(f"No executor found for tool: {tool_name}")
        
        # Defensive: Handle malformed tool_params from confused models
        # Expected: {"param_name": value} e.g. {"days_back": 30}
        # Malformed: {"key": "param_name", "value": value, ...}
        if tool_params and isinstance(tool_params, dict):
            if 'key' in tool_params and 'value' in tool_params:
                tool_params = {tool_params['key']: tool_params['value']}
        
        # Call executor with params if it accepts them
        if tool_params:
            return executor(**tool_params)
        else:
            return executor()

    def get_available_tools(self, user_role: str = "user") -> list[dict]:
        """
        Returns list of tools available for data visualization.
        Filtered by user's permission level.
        
        Args:
            user_role: The user's role
            
        Returns:
            List of tool definitions for data page
        """
        return get_data_tools(user_role)
