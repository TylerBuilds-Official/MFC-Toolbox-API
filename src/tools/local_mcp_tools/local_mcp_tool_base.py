import asyncio
import inspect
from src.tools.local_mcp_tools.local_mcp_tool_getJobInfo import oa_get_job_info
from src.tools.local_mcp_tools.local_mcp_tool_getAllJobInfo import oa_get_jobs
from src.tools.local_mcp_tools.local_mcp_tool_getMachineProductionData import oa_get_machine_production
from src.tools.local_mcp_tools.local_mcp_tool_getOTHoursByJob import oa_get_ot_hours_by_job
from src.tools.local_mcp_tools.local_mcp_tool_getOTHoursAllJobs import oa_get_ot_hours_all_jobs
from src.tools.local_mcp_tools.local_mcp_tool_searchUserMemories import oa_search_user_memories
from src.tools.local_mcp_tools.local_mcp_tool_saveUserMemory import oa_save_user_memory
from src.tools.local_mcp_tools.local_mcp_tool_updateUserMemory import oa_update_user_memory
from src.tools.local_mcp_tools.local_mcp_tool_deleteUserMemory import oa_delete_user_memory
from src.tools.local_mcp_tools.local_mcp_tool_getAllUserMemories import oa_get_all_user_memories
from src.tools.local_mcp_tools.local_mcp_tool_searchConversations import oa_search_conversations
from src.tools.local_mcp_tools.local_mcp_tool_getRecentConversations import oa_get_recent_conversations
from src.tools.local_mcp_tools.local_mcp_tool_getConversationMessages import oa_get_conversation_messages
from src.tools.local_mcp_tools.local_mcp_tool_getActiveJobs import oa_get_active_jobs
from src.tools.local_mcp_tools.local_mcp_tool_getJobsByPM import oa_get_jobs_by_pm
from src.tools.local_mcp_tools.local_mcp_tool_getJobsShippingSoon import oa_get_jobs_shipping_soon
from src.tools.local_mcp_tools.local_mcp_tool_createDataArtifact import oa_create_data_artifact
from src.tools.local_mcp_tools.local_mcp_tool_searchDataSessions import oa_search_data_sessions
from src.tools.local_mcp_tools.local_mcp_tool_getDataSessions import oa_get_data_sessions
from src.tools.local_mcp_tools.local_mcp_tool_getDataSessionDetails import oa_get_data_session_details

from src.tools.local_mcp_tools.company_data import (oa_get_all_company_data,
                                                    oa_get_company_info,
                                                    oa_get_contact_info,
                                                    oa_get_department_summary,
                                                    oa_get_employee_directory_summary,
                                                    oa_get_employee,
                                                    oa_get_employees_by_department,
                                                    oa_get_it_team,
                                                    oa_get_project_managers,
                                                    oa_list_departments,
                                                    oa_search_employees,
                                                    )

# Filesystem Tools (Agent Connector) - These are async!
from src.tools.local_mcp_tools.filesystem_tools import (
    oa_fs_list_directory,
    oa_fs_read_file,
    oa_fs_write_file,
    oa_fs_delete_file,
    oa_fs_get_allowed_folders,
    ASYNC_TOOLS,
)

# Import permission checking from centralized registry
from src.tools.tool_registry import get_tool, can_use_tool


class OAToolBase:
    """
    Tool dispatcher for LLM function calling.
    
    Handles routing tool calls to their executors and injecting
    server-side context (like user_id) for tools that need it.
    
    Supports both sync and async tools. Use dispatch_async() when
    calling from async context to properly await async tools.
    """
    
    TOOL_REGISTRY = {
        'get_job_info':                 oa_get_job_info,
        'get_all_job_info':             oa_get_jobs,
        'get_machine_production':       oa_get_machine_production,
        'get_ot_hours_by_job':          oa_get_ot_hours_by_job,
        'get_ot_hours_all_jobs':        oa_get_ot_hours_all_jobs,
        'search_user_memories':         oa_search_user_memories,
        'get_active_jobs':              oa_get_active_jobs,


        'get_jobs_by_pm':               oa_get_jobs_by_pm,
        "get_jobs_shipping_soon":       oa_get_jobs_shipping_soon,


        # Internal tools / Non-callable by user
        'save_user_memory':             oa_save_user_memory,
        'update_user_memory':           oa_update_user_memory,
        'delete_user_memory':           oa_delete_user_memory,
        'get_all_user_memories':        oa_get_all_user_memories,
        'search_conversations':         oa_search_conversations,
        'get_recent_conversations':     oa_get_recent_conversations,
        'get_conversation_messages':    oa_get_conversation_messages,
        'create_data_artifact':         oa_create_data_artifact,
        'search_data_sessions':         oa_search_data_sessions,
        'get_data_sessions':            oa_get_data_sessions,
        'get_data_session_details':     oa_get_data_session_details,


        # Employee / Company data tools
        'get_all_company_data':             oa_get_all_company_data,
        'get_company_info':                 oa_get_company_info,
        'get_contact_info':                 oa_get_contact_info,
        'get_department_summary':           oa_get_department_summary,
        'get_employee_directory_summary':   oa_get_employee_directory_summary,
        'get_employee':                     oa_get_employee,
        'get_employees_by_department':      oa_get_employees_by_department,
        'get_it_team':                      oa_get_it_team,
        'get_project_managers':             oa_get_project_managers,
        'list_departments':                 oa_list_departments,
        'search_employees':                 oa_search_employees,

        # Filesystem Tools (Agent Connector) - async tools
        'fs_list_directory':                oa_fs_list_directory,
        'fs_read_file':                     oa_fs_read_file,
        'fs_write_file':                    oa_fs_write_file,
        'fs_delete_file':                   oa_fs_delete_file,
        'fs_get_allowed_folders':           oa_fs_get_allowed_folders,
    }
    
    # Tools that need user_id injected
    USER_ID_TOOLS = {
        'search_user_memories',
        'save_user_memory',
        'update_user_memory',
        'delete_user_memory',
        'get_all_user_memories',

        'search_conversations',
        'get_recent_conversations',
        'get_conversation_messages',

        'create_data_artifact',
        'search_data_sessions',
        'get_data_sessions',
        'get_data_session_details',

        # Filesystem tools need user_id for permission checking
        'fs_list_directory',
        'fs_read_file',
        'fs_write_file',
        'fs_delete_file',
        'fs_get_allowed_folders',
    }
    
    # Tools that also need conversation_id injected
    CONVERSATION_ID_TOOLS = {
        'save_user_memory',
        'create_data_artifact',
    }

    def _prepare_dispatch(self, name: str, context: dict = None, **kwargs):
        """
        Common preparation for dispatch - checks permissions, injects context.
        
        Returns:
            Tuple of (executor, kwargs) or (None, error_dict)
        """
        # Check if tool exists in executor registry
        if name not in self.TOOL_REGISTRY:
            return None, {"error": f"Tool '{name}' not found."}

        # Permission check (defense in depth)
        user_role = context.get("user_role", "pending") if context else "pending"
        tool_def = get_tool(name)

        if tool_def:
            # Tool is in the centralized registry - check permissions
            if not can_use_tool(user_role, tool_def["category"]):
                return None, {
                    "error": f"Permission denied: insufficient privileges for tool '{name}'."
                }

        # Inject context for tools that need it
        if context:
            if name in self.USER_ID_TOOLS and 'user_id' in context:
                kwargs['user_id'] = context['user_id']
            if name in self.CONVERSATION_ID_TOOLS and 'conversation_id' in context:
                kwargs['conversation_id'] = context['conversation_id']

        return self.TOOL_REGISTRY[name], kwargs

    def dispatch(self, name: str, context: dict = None, **kwargs):
        """
        Dispatch a tool call to its executor (sync version).
        
        WARNING: This will NOT properly handle async tools!
        Use dispatch_async() from async contexts.

        Args:
            name: Name of the tool to execute
            context: Server-side context (user_id, user_role, conversation_id, etc.)
            **kwargs: Tool parameters from LLM

        Returns:
            Tool execution result
        """
        executor, kwargs_or_error = self._prepare_dispatch(name, context, **kwargs)
        
        if executor is None:
            return kwargs_or_error  # This is the error dict
        
        # Check if tool is async
        if name in ASYNC_TOOLS:
            # Try to run in event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Can't await from sync context when loop is running
                    # This is a limitation - caller should use dispatch_async
                    return {"error": f"Tool '{name}' is async and must be called from async context. Use dispatch_async()."}
                else:
                    return loop.run_until_complete(executor(**kwargs_or_error))
            except RuntimeError:
                return asyncio.run(executor(**kwargs_or_error))
        
        return executor(**kwargs_or_error)

    async def dispatch_async(self, name: str, context: dict = None, **kwargs):
        """
        Dispatch a tool call to its executor (async version).
        
        Use this from async contexts to properly handle async tools.

        Args:
            name: Name of the tool to execute
            context: Server-side context (user_id, user_role, conversation_id, etc.)
            **kwargs: Tool parameters from LLM

        Returns:
            Tool execution result
        """
        executor, kwargs_or_error = self._prepare_dispatch(name, context, **kwargs)
        
        if executor is None:
            return kwargs_or_error  # This is the error dict
        
        # Check if tool is async
        if name in ASYNC_TOOLS or asyncio.iscoroutinefunction(executor):
            return await executor(**kwargs_or_error)
        else:
            # Run sync tool in executor to not block event loop
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: executor(**kwargs_or_error))
    
    def is_async_tool(self, name: str) -> bool:
        """Check if a tool requires async execution."""
        return name in ASYNC_TOOLS
