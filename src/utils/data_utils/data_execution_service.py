"""
Orchestrates tool execution, normalization, and result storage.

This is the central service that ties together:
- Tool registry (single source of truth)
- Result normalization
- Database storage
- Status management
- Title/Summary generation (AI-powered via Anthropic)
"""
import os
from typing import Any
from src.utils.data_utils.data_session_service import DataSessionService
from src.utils.data_utils.data_result_service import DataResultService
from src.utils.data_utils.tool_normalizer import ToolNormalizer
from src.utils.data_utils.data_session import DataSession
from src.utils.data_utils.data_result import DataResult, NormalizedResult
from src.utils.data_utils.summary_helper import DataSummaryHelper
from src.tools.anthropic_chat.client import AnthropicClient

# Import from centralized utilities
from src.tools.tool_utils import (
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
        # Initialize Anthropic client for title/summary generation
        api_key = os.getenv("ANTHROPIC_API_KEY")
        self._anthropic_client = AnthropicClient(api_key=api_key).client if api_key else None

    def execute(
        self, 
        session_id: int, 
        user_role: str = "user",
        user_specialties: list[str] = None
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
            user_role: The user's base role for permission checking
            user_specialties: List of specialty roles the user has
            
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
        
        # Check permissions (role OR specialty)
        if not can_use_tool(user_role, tool["category"], user_specialties):
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
            
            # Generate title using AI
            self._generate_and_save_title(session, result)
            
            # Generate summary using AI
            self._generate_and_save_summary(session, result)
            
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
        user_role: str = "user",
        user_specialties: list[str] = None
    ) -> NormalizedResult:
        """
        Executes a tool and returns normalized result without storing.
        Useful for previewing what a tool will return.
        
        Args:
            tool_name: The tool to execute
            tool_params: Tool parameters
            user_role: The user's base role for permission checking
            user_specialties: List of specialty roles the user has
            
        Returns:
            NormalizedResult (not persisted)
            
        Raises:
            PermissionError: If user lacks permission
        """
        # Get tool and check permissions
        tool = get_tool(tool_name)
        if tool is None:
            raise ValueError(f"Unknown tool: {tool_name}")
            
        if not can_use_tool(user_role, tool["category"], user_specialties):
            raise PermissionError(
                f"Role '{user_role}' does not have permission to use tool '{tool_name}'"
            )
        
        raw_result = self._execute_tool(tool_name, tool_params)
        return self.normalizer.normalize(tool_name, raw_result)

    @staticmethod
    def _execute_tool(tool_name: str, tool_params: dict = None) -> Any:
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

    @staticmethod
    def get_available_tools(user_role: str = "user", user_specialties: list[str] = None) -> list[dict]:
        """
        Returns list of tools available for data visualization.
        Filtered by user's permission level and specialties.
        
        Args:
            user_role: The user's base role
            user_specialties: List of specialty roles the user has
            
        Returns:
            List of tool definitions for data page
        """
        return get_data_tools(user_role, user_specialties)

    def _generate_and_save_title(self, session: DataSession, result: DataResult) -> None:
        """
        Generates an AI-powered title for the session and saves it.
        Fails silently if title generation fails.
        
        Args:
            session: The data session
            result: The execution result
        """
        if not self._anthropic_client:
            print("[DataExecutionService] No Anthropic client available for title generation")
            return
        
        try:
            # Build session dict for title generation
            session_dict = {
                "messages": {
                    "tool_name": session.tool_name,
                    "tool_params": session.tool_params,
                    "row_count": result.row_count if result else 0,
                    "columns": result.columns if result else [],
                }
            }
            
            title = DataSummaryHelper.generate_title(
                session_dict=session_dict,
                client=self._anthropic_client,
                provider="anthropic"
            )
            
            if title:
                DataSessionService.set_title(session.id, title)
                print(f"[DataExecutionService] Generated title for session {session.id}: {title}")
            
        except Exception as e:
            print(f"[DataExecutionService] Title generation failed for session {session.id}: {e}")

    def _generate_and_save_summary(self, session: DataSession, result: DataResult) -> None:
        """
        Generates an AI-powered summary for the session tooltip and saves it.
        Fails silently if summary generation fails.
        
        Args:
            session: The data session
            result: The execution result
        """
        if not self._anthropic_client:
            print("[DataExecutionService] No Anthropic client available for summary generation")
            return
        
        try:
            # Build session dict for summary generation
            # Include sample data for context
            sample_rows = result.rows[:5] if result and result.rows else []
            
            session_dict = {
                "tool_name": session.tool_name,
                "tool_params": session.tool_params,
                "row_count": result.row_count if result else 0,
                "columns": result.columns if result else [],
                "sample_data": sample_rows,
            }
            
            summary = DataSummaryHelper.ai_data_session_summary(
                session_dict=session_dict,
                client=self._anthropic_client,
                provider="anthropic"
            )
            
            if summary:
                DataSessionService.set_summary(session.id, summary)
                print(f"[DataExecutionService] Generated summary for session {session.id}: {summary}")
            
        except Exception as e:
            print(f"[DataExecutionService] Summary generation failed for session {session.id}: {e}")
