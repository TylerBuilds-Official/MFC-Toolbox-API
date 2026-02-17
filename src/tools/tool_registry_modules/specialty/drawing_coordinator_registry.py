"""
Drawing Coordinator Tools Registry

Requires: 'drawing_coordinator' specialty role
Display Category: Drawing Coordinator
"""

from src.tools.specialty_tools.drawing_coordinator import (
    oa_dc_scan_downloads_for_transmittals,
    oa_dc_process_transmittal,
    oa_dc_get_default_output_path,
)


DC_TOOLS = [
    {
        "name": "scan_downloads_for_transmittals",
        "description": (
            "Scan the user's Downloads folder for recent transmittal ZIP files. "
            "Use after manual downloads from cloud links (SharePoint, WeTransfer, etc.)."
        ),
        "category": "transmittal_processing",
        "display_category": "Drawing Coordinator",

        "parameters": {
            "type": "object",
            "properties": {
                "job_number": {
                    "type": "string",
                    "description": "Optional filter by 4-digit job number",
                },
                "minutes_ago": {
                    "type": "integer",
                    "description": "Look back window in minutes (default 15, max 120)",
                },
            },
            "required": [],
        },

        "executor":      oa_dc_scan_downloads_for_transmittals,
        "is_async":      True,
        "needs_user_id": True,

        "chat_toolbox":       True,
        "data_visualization": False,
    },

    {
        "name": "process_transmittal",
        "description": (
            "Process a transmittal ZIP through the full pipeline — extract, classify, "
            "organize, and optionally distribute to network destinations. "
            "Output defaults to ~/Desktop/Fabcore/DrawingCoordinatorTools/Transmittals."
        ),
        "category": "transmittal_processing",
        "display_category": "Drawing Coordinator",

        "parameters": {
            "type": "object",
            "properties": {
                "zip_path": {
                    "type": "string",
                    "description": "Full path to the transmittal ZIP file",
                },
                "output_path": {
                    "type": "string",
                    "description": "Output directory. Uses default if omitted.",
                },
                "job_number": {
                    "type": "string",
                    "description": "4-digit job number. Auto-detected if omitted.",
                },
                "distribute_data": {
                    "type": "boolean",
                    "description": "Distribute to network destinations (default true)",
                },
            },
            "required": ["zip_path"],
        },

        "executor":      oa_dc_process_transmittal,
        "is_async":      True,
        "needs_user_id": True,

        "chat_toolbox":       True,
        "data_visualization": False,
    },

    {
        "name": "get_transmittal_output_path",
        "description": "Get the default output path for transmittal processing.",
        "category": "transmittal_processing",
        "display_category": "Drawing Coordinator",

        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },

        "executor":      oa_dc_get_default_output_path,
        "is_async":      True,
        "needs_user_id": True,

        "chat_toolbox":       False,
        "data_visualization": False,
    },
]


__all__ = ["DC_TOOLS"]
