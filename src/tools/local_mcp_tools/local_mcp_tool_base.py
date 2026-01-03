from src.tools.local_mcp_tools.local_mcp_tool_getJobInfo import oa_get_job_info
from src.tools.local_mcp_tools.local_mcp_tool_getAllJobInfo import oa_get_jobs
from src.tools.local_mcp_tools.local_mcp_tool_getMachineProductionData import oa_get_machine_production
from src.tools.local_mcp_tools.local_mcp_tool_getOTHoursByJob import oa_get_ot_hours_by_job
from src.tools.local_mcp_tools.local_mcp_tool_getOTHoursAllJobs import oa_get_ot_hours_all_jobs
from src.tools.local_mcp_tools.local_mcp_tool_searchUserMemories import oa_search_user_memories
from src.tools.local_mcp_tools.local_mcp_tool_saveUserMemory import oa_save_user_memory
from src.tools.local_mcp_tools.local_mcp_tool_searchConversations import oa_search_conversations
from src.tools.local_mcp_tools.local_mcp_tool_getRecentConversations import oa_get_recent_conversations
from src.tools.local_mcp_tools.local_mcp_tool_getConversationMessages import oa_get_conversation_messages
from src.tools.local_mcp_tools.local_mcp_tool_getActiveJobs import oa_get_active_jobs
from src.tools.local_mcp_tools.local_mcp_tool_getJobsByPM import oa_get_jobs_by_pm
from src.tools.local_mcp_tools.local_mcp_tool_getJobsShippingSoon import oa_get_jobs_shipping_soon


# Import permission checking from centralized registry
from src.tools.tool_registry import get_tool, can_use_tool


class OAToolBase:
    """
    Tool dispatcher for LLM function calling.
    
    Handles routing tool calls to their executors and injecting
    server-side context (like user_id) for tools that need it.
    """
    
    TOOL_REGISTRY = {
        'get_job_info': oa_get_job_info,
        'get_all_job_info': oa_get_jobs,
        'get_machine_production': oa_get_machine_production,
        'get_ot_hours_by_job': oa_get_ot_hours_by_job,
        'get_ot_hours_all_jobs': oa_get_ot_hours_all_jobs,
        'search_user_memories': oa_search_user_memories,
        'get_active_jobs': oa_get_active_jobs,

        # REMOVED:
        # 'get_job_details': oa_get_job_details,

        'get_jobs_by_pm': oa_get_jobs_by_pm,
        "get_jobs_shipping_soon": oa_get_jobs_shipping_soon,

        # Non - Callable
        'save_user_memory': oa_save_user_memory,
        'search_conversations': oa_search_conversations,
        'get_recent_conversations': oa_get_recent_conversations,
        'get_conversation_messages': oa_get_conversation_messages,
    }
    
    # Tools that need user_id injected
    USER_ID_TOOLS = {
        'search_user_memories',
        'save_user_memory',
        'search_conversations',
        'get_recent_conversations',
        'get_conversation_messages',
    }
    
    # Tools that also need conversation_id injected
    CONVERSATION_ID_TOOLS = {
        'save_user_memory',
    }

    def dispatch(self, tool_name: str, context: dict = None, **kwargs):
        """
        Dispatch a tool call to its executor.
        
        Args:
            tool_name: Name of the tool to execute
            context: Server-side context (user_id, user_role, conversation_id, etc.)
                     Injected for tools that need it, not provided by LLM
            **kwargs: Tool parameters from LLM
            
        Returns:
            Tool execution result
        """
        # Check if tool exists in executor registry
        if tool_name not in self.TOOL_REGISTRY:
            return {"error": f"Tool '{tool_name}' not found."}
        
        # Permission check (defense in depth)
        user_role = context.get("user_role", "pending") if context else "pending"
        tool_def = get_tool(tool_name)
        
        if tool_def:
            # Tool is in the centralized registry - check permissions
            if not can_use_tool(user_role, tool_def["category"]):
                return {
                    "error": f"Permission denied: insufficient privileges for tool '{tool_name}'."
                }
        # Note: Tools not yet in centralized registry are allowed through
        # TODO: Migrate all tools to centralized registry for full coverage
        
        # Inject context for tools that need it
        if context:
            if tool_name in self.USER_ID_TOOLS and 'user_id' in context:
                kwargs['user_id'] = context['user_id']
            if tool_name in self.CONVERSATION_ID_TOOLS and 'conversation_id' in context:
                kwargs['conversation_id'] = context['conversation_id']
        
        return self.TOOL_REGISTRY[tool_name](**kwargs)
