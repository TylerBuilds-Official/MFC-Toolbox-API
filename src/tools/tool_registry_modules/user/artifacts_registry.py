"""
Artifacts Tools Registry - User Level

Accessible by: user, manager, admin
Category: artifacts
Display Category: Artifacts

AI-internal tools for creating data visualization artifacts.
Artifacts are clickable cards in chat that open full visualization pages.
"""

from src.tools.local_mcp_tools.local_mcp_tool_createDataArtifact import oa_create_data_artifact


ARTIFACT_TOOLS = [
    {
        "name": "create_data_artifact",
        "description": "Create a clickable data visualization card in the chat response. Use this when the user asks for data that would benefit from interactive visualization - job info, production reports, overtime summaries, etc. The artifact appears as a card the user can click to open a full data visualization page. Use parent_session_id when re-running or refining a previous query to maintain lineage.",
        "category": "artifacts",
        "display_category": "Artifacts",

        "parameters": {
            "type": "object",
            "properties": {
                "target_tool": {
                    "type": "string",
                    "description": "The data tool to use (e.g., 'get_job_info', 'get_machine_production', 'get_ot_hours_by_job')"
                },
                "tool_params": {
                    "type": "object",
                    "description": "A flat dict mapping parameter names to values. Example: {'job_number': '6516'} or {'days_back': 30}. Do NOT use nested key/value structures."
                },
                "chart_type": {
                    "type": "string",
                    "enum": ["bar", "line", "pie", "table", "card"],
                    "description": "Suggested visualization type (optional - uses tool default if not specified)"
                },
                "title": {
                    "type": "string",
                    "description": "Custom title for the artifact card (optional - auto-generated if not provided)"
                },
                "parent_session_id": {
                    "type": "integer",
                    "description": "Optional parent session ID for lineage tracking. Use when re-running or refining a previous query to link the new session to its parent."
                }
            },
            "required": ["target_tool"]
        },

        "executor": oa_create_data_artifact,
        "chat_toolbox": False,
        "data_visualization": False,
        "needs_user_id": True,
        "needs_conversation_id": True,
    },
]
