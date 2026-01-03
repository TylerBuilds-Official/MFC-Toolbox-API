"""
Create Data Artifact Tool

LLM calls this to create a clickable data visualization card in chat.
Returns artifact ID for embedding in the response.
"""
from src.utils.artifact_utils import (
    ArtifactService,
    ArtifactGenerationParams,
    ArtifactGenerationResults,
)


def oa_create_data_artifact(
    target_tool: str,
    tool_params: dict = None,
    chart_type: str = None,
    title: str = None,
    job_number: str = None,
    # Context injected by tool dispatcher
    user_id: int = None,
    conversation_id: int = None,
    **kwargs
) -> dict:
    """
    Create a data artifact that can be clicked to open a visualization.
    
    Args:
        target_tool: The data tool to execute (e.g., 'get_job_info', 'get_machine_production')
        tool_params: Parameters for the tool (e.g., {'job_number': '6516'})
        chart_type: Suggested visualization type (bar, line, pie, table, card)
        title: Optional custom title (auto-generated if not provided)
        job_number: Job number for traceability (extracted from params if not provided)
        
    Returns:
        Dict with artifact_id and suggested embed marker
    """
    if not user_id or not conversation_id:
        return {"error": "Missing context (user_id or conversation_id)"}

    from src.tools.tool_registry import get_tool
    # Validate tool exists and is data-visualizable
    tool_def = get_tool(target_tool)
    if not tool_def:
        return {"error": f"Unknown tool: {target_tool}"}
    
    if not tool_def.get("data_visualization", False):
        return {"error": f"Tool '{target_tool}' does not support data visualization"}
    
    # Extract job_number from params if not explicitly provided
    if not job_number and tool_params:
        job_number = tool_params.get("job_number") or tool_params.get("job")
    
    # Auto-generate title if not provided
    if not title:
        title = _generate_title(target_tool, tool_params, job_number)
    
    # Use tool's default chart type if not specified
    if not chart_type:
        chart_type = tool_def.get("default_chart_type", "bar")
    
    # Get chart config hints from tool definition
    chart_config = tool_def.get("chart_config", {})
    
    # Build generation params
    gen_params = ArtifactGenerationParams(
        tool_name    = target_tool,
        tool_params  = tool_params or {},
        chart_type   = chart_type,
        x_axis       = chart_config.get("x_axis"),
        y_axis       = chart_config.get("y_axis"),
        group_by     = chart_config.get("series_by"),
        job_number   = job_number,
    )
    
    # Create artifact
    artifact = ArtifactService.create_artifact(
        user_id          = user_id,
        conversation_id  = conversation_id,
        artifact_type    = "data",
        title            = title,
        generation_params = gen_params,
        status           = "ready",
    )
    
    # Return info for LLM to embed in response
    return {
        "success": True,
        "artifact_id": artifact.id,
        "title": artifact.title,
        "embed_marker": f'<artifact id="{artifact.id}" type="data" title="{artifact.title}" />',
        "instructions": "Include the embed_marker in your response where you want the artifact card to appear."
    }


def _generate_title(tool_name: str, tool_params: dict, job_number: str = None) -> str:
    """Generate a sensible title from tool info."""
    
    # Job-specific titles
    if job_number:
        tool_labels = {
            "get_job_info": f"Job {job_number} Details",
            "get_ot_hours_by_job": f"Job {job_number} Overtime",
        }
        if tool_name in tool_labels:
            return tool_labels[tool_name]
        return f"Job {job_number} Data"
    
    # Generic titles by tool
    tool_labels = {
        "get_all_job_info": "All Jobs",
        "get_active_jobs": "Active Jobs",
        "get_machine_production": "Machine Production",
        "get_ot_hours_all_jobs": "Overtime Summary",
        "get_jobs_by_pm": f"Jobs by {tool_params.get('pm_name', 'PM')}" if tool_params else "Jobs by PM",
        "get_jobs_shipping_soon": "Upcoming Shipments",
    }
    
    if tool_name in tool_labels:
        return tool_labels[tool_name]
    
    # Fallback: convert tool_name to title case
    return tool_name.replace("_", " ").title()


__all__ = ['oa_create_data_artifact']
