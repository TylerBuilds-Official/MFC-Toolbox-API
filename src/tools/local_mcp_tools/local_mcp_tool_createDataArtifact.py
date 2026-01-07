"""
Create Data Artifact Tool

LLM calls this to create a clickable data visualization card in chat.
Returns artifact ID for embedding in the response.
"""
from src.utils.artifact_utils import (
    ArtifactService,
    ArtifactGenerationParams
)


def oa_create_data_artifact(
    target_tool: str,
    tool_params: dict = None,
    chart_type: str = None,
    title: str = None,
    job_number: str = None,
    parent_session_id: int = None,
    # Context injected by tool dispatcher
    user_id: int = None,
    conversation_id: int = None,
    **kwargs
) -> dict:
    """
    Create a data artifact that can be clicked to open a visualization.
    
    Args:
        target_tool: The data tool to execute (e.g., 'get_job_info', 'get_machine_production')
        tool_params: A flat dictionary mapping parameter names directly to their values.
                     Format: {"param_name": value, ...}
                     Examples:
                       - {"job_number": "6516"}
                       - {"days_back": 30}
                       - {"pm_name": "John Smith", "active_only": true}
                     Do NOT use nested structures like {"key": "...", "value": "..."}.

        chart_type: Suggested visualization type (bar, line, pie, table, card)
        title: Optional custom title (auto-generated if not provided)
        job_number: Job number for traceability (extracted from params if not provided)
        parent_session_id: Optional parent session ID for lineage tracking.
                           Use this when re-running or refining a previous query.
                           The new session will be linked to the parent in a chain.

    Returns:
        Dict with artifact_id and suggested embed marker


    Example hinting for data visualization calls:

        json {
          "target_tool": "get_machine_production",
          "tool_params": {
            "days_back": 60
        },
          "chart_type": "line",
          "title": "60-Day Machine Production"
        }

    Or for overtime by job:

        json {
          "target_tool": "get_ot_hours_by_job",
          "tool_params": {
            "job_number": "6516",
            "start_date": "2025-01-01",
            "end_date": "2025-01-31"
          },
          "chart_type": "bar",
          "title": "Job 6516 January Overtime"
        }
        
    Re-running a previous query with lineage:
    
        json {
          "target_tool": "get_machine_production",
          "tool_params": {
            "days_back": 30
          },
          "parent_session_id": 123,
          "title": "Updated Machine Production"
        }


    """
    if not user_id or not conversation_id:
        return {"error": "Missing context (user_id or conversation_id)"}

    # Defensive: Handle malformed tool_params from confused models
    # Expected: {"param_name": value} e.g. {"days_back": 30}
    # Malformed: {"key": "param_name", "value": value, ...}
    if tool_params and isinstance(tool_params, dict):
        if 'key' in tool_params and 'value' in tool_params:
            tool_params = {tool_params['key']: tool_params['value']}

    from src.tools.tool_registry import get_tool
    # Validate tool exists and is data-visualizable
    tool_def = get_tool(target_tool)
    if not tool_def:
        return {"error": f"Unknown tool: {target_tool}"}
    
    if not tool_def.get("data_visualization", False):
        return {"error": f"Tool '{target_tool}' does not support data visualization"}
    
    # Validate parent_session_id if provided
    if parent_session_id is not None:
        from src.tools.sql_tools import get_data_session
        parent = get_data_session(parent_session_id, user_id)
        if not parent:
            return {"error": f"Parent session {parent_session_id} not found or access denied"}
    
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
        tool_name         = target_tool,
        tool_params       = tool_params or {},
        chart_type        = chart_type,
        x_axis            = chart_config.get("x_axis"),
        y_axis            = chart_config.get("y_axis"),
        group_by          = chart_config.get("series_by"),
        job_number        = job_number,
        parent_session_id = parent_session_id,
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
    
    # Build response
    response = {
        "success": True,
        "artifact_id": artifact.id,
        "title": artifact.title,
        "embed_marker": f'<artifact id="{artifact.id}" type="data" title="{artifact.title}" />',
        "instructions": "Include the embed_marker in your response where you want the artifact card to appear."
    }
    
    # Note lineage if parent was provided
    if parent_session_id:
        response["lineage_note"] = f"This artifact is linked to parent session {parent_session_id}"
    
    return response


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
