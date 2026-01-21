"""
Drawing Coordinator Tools Registry

Requires: 'drawing_coordinator' specialty role
Categories: transmittal_processing, drawing_classification, drawing_distribution
Display Category: Drawing Coordinator

Tools for processing steel fabrication transmittals - extracting ZIPs,
classifying drawings, organizing output, and distributing to network locations.
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
            "Use this after the user has manually downloaded files from cloud storage links "
            "(SharePoint, WeTransfer, Dropbox, etc.) to find transmittals ready for processing. "
            "Returns a list of ZIP files with detected job numbers, transmittal numbers, and types. "
            "Call process_transmittal for each file that should be processed."
        ),
        "category": "transmittal_processing",
        "display_category": "Drawing Coordinator",
        
        "parameters": {
            "type": "object",
            "properties": {
                "job_number": {
                    "type": "string",
                    "description": "Optional filter - only return files matching this 4-digit job number"
                },
                "minutes_ago": {
                    "type": "integer",
                    "description": "Only look at files modified in the last N minutes (default 15, max 120)"
                }
            },
            "required": []
        },
        
        "executor": oa_dc_scan_downloads_for_transmittals,
        "is_async": True,
        "needs_user_id": True,
        
        # UI visibility
        "chat_toolbox": True,
        "data_visualization": False,
    },
    
    {
        "name": "process_transmittal",
        "description": (
            "Process a transmittal ZIP file through the full drawing coordinator pipeline. "
            "Extracts the ZIP, detects job number and transmittal number, classifies files "
            "(fabrication drawings, erection drawings, NC files, etc.), builds organized "
            "output folder structure, creates cover sheet PDF, and optionally distributes "
            "files to network destinations (SD drive, NC drive). "
            "Use this when the user has a new transmittal ZIP to process."
        ),
        "category": "transmittal_processing",
        "display_category": "Drawing Coordinator",
        
        "parameters": {
            "type": "object",
            "properties": {
                "zip_path": {
                    "type": "string",
                    "description": "Full path to the transmittal ZIP file to process"
                },
                "output_path": {
                    "type": "string",
                    "description": "Directory where processed output should be saved. Defaults to ~/Desktop/Fabcore/DrawingCoordinatorTools/Output if not provided."
                },
                "job_number": {
                    "type": "string",
                    "description": "4-digit job number (e.g., '6516'). If not provided, will attempt to auto-detect from ZIP filename or contents."
                },
                "distribute_data": {
                    "type": "boolean",
                    "description": "Whether to distribute files to network destinations (SD drive, NC drive). Defaults to true."
                }
            },
            "required": ["zip_path"]
        },
        
        "executor": oa_dc_process_transmittal,
        "is_async": True,
        "needs_user_id": True,
        
        # UI visibility
        "chat_toolbox": True,
        "data_visualization": False,
    },
    
    {
        "name": "get_transmittal_output_path",
        "description": (
            "Get the default output path where transmittal processing saves files. "
            "Useful for checking where files will be saved before processing."
        ),
        "category": "transmittal_processing",
        "display_category": "Drawing Coordinator",
        
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },
        
        "executor": oa_dc_get_default_output_path,
        "is_async": True,
        "needs_user_id": True,
        
        # UI visibility
        "chat_toolbox": False,  # Helper tool, not shown in UI
        "data_visualization": False,
    },
]


__all__ = ["DC_TOOLS"]
