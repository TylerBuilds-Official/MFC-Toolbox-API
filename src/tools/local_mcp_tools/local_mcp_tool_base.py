from src.tools.local_mcp_tools.local_mcp_tool_getJobInfo import oa_get_job_info
from src.tools.local_mcp_tools.local_mcp_tool_getAllJobInfo import oa_get_jobs
from src.tools.local_mcp_tools.local_mcp_tool_getMachineProductionData import oa_get_machine_production
from src.tools.local_mcp_tools.local_mcp_tool_searchUserMemories import oa_search_user_memories
from src.tools.local_mcp_tools.local_mcp_tool_saveUserMemory import oa_save_user_memory


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
        'search_user_memories': oa_search_user_memories,
        'save_user_memory': oa_save_user_memory,
    }
    
    # Tools that need user_id injected
    USER_ID_TOOLS = {
        'search_user_memories',
        'save_user_memory',
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
            context: Server-side context (user_id, conversation_id, etc.)
                     Injected for tools that need it, not provided by LLM
            **kwargs: Tool parameters from LLM
            
        Returns:
            Tool execution result
        """
        if tool_name in self.TOOL_REGISTRY:
            # Inject context for tools that need it
            if context:
                if tool_name in self.USER_ID_TOOLS and 'user_id' in context:
                    kwargs['user_id'] = context['user_id']
                if tool_name in self.CONVERSATION_ID_TOOLS and 'conversation_id' in context:
                    kwargs['conversation_id'] = context['conversation_id']
            
            return self.TOOL_REGISTRY[tool_name](**kwargs)
        else:
            return {"error": f"Tool {tool_name} not found."}
