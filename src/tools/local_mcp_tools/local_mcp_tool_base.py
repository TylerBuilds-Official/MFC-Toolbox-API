from src.tools.local_mcp_tools.local_mcp_tool_getJobInfo import oa_get_job_info
from src.tools.local_mcp_tools.local_mcp_tool_getAllJobInfo import oa_get_jobs
from src.tools.local_mcp_tools.local_mcp_tool_getMachineProductionData import oa_get_machine_production


class OAToolBase:
    TOOL_REGISTRY = {
        'get_job_info': oa_get_job_info,
        'get_all_job_info': oa_get_jobs,
        'get_machine_production': oa_get_machine_production
    }

    def dispatch(self, tool_name: str, **kwargs):
        if tool_name in self.TOOL_REGISTRY:
            return self.TOOL_REGISTRY[tool_name](**kwargs)
        else:
            return { "error": f"Tool {tool_name} not found."}

