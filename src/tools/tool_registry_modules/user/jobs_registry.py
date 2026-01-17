"""
Jobs Tools Registry - User Level

Accessible by: user, manager, admin
Categories: job_read, reports
Display Categories: Jobs, Production

Tools for viewing job information, status, and production data.
"""

from src.tools.local_mcp_tools.local_mcp_tool_getAllJobInfo import oa_get_jobs
from src.tools.local_mcp_tools.local_mcp_tool_getJobInfo import oa_get_job_info
from src.tools.local_mcp_tools.local_mcp_tool_getMachineProductionData import oa_get_machine_production
from src.tools.local_mcp_tools.local_mcp_tool_getActiveJobs import oa_get_active_jobs
from src.tools.local_mcp_tools.local_mcp_tool_getJobsByPM import oa_get_jobs_by_pm
from src.tools.local_mcp_tools.local_mcp_tool_getJobsShippingSoon import oa_get_jobs_shipping_soon


JOB_TOOLS = [
    {
        "name": "get_all_job_info",
        "description": "Get a list of all jobs with basic info (job number, name, contractor, location, etc.)",
        "category": "job_read",
        "display_category": "Jobs",

        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },

        "executor": oa_get_jobs,
        "chat_toolbox": True,
        "data_visualization": True,
        "default_chart_type": "table",
        "normalizer": "job_list",
    },


    {
        "name": "get_job_info",
        "description": "Get comprehensive job information including hours, dates, financials, production data (pieces/weight), and status. Merges data from Tekla and ScheduleShare.",
        "category": "job_read",
        "display_category": "Jobs",

        "parameters": {
            "type": "object",
            "properties": {
                "job_number": {
                    "type": "string",
                    "description": "The job number to retrieve information for (e.g. 6516)"
                }
            },
            "required": ["job_number"]
        },

        "executor": oa_get_job_info,
        "chat_toolbox": True,
        "data_visualization": True,
        "default_chart_type": "card",
    },


    {
        "name": "get_machine_production",
        "description": "Get daily production counts per CNC machine (pieces processed and total weight) over a date range.",
        "category": "reports",
        "display_category": "Production",

        "parameters": {
            "type": "object",
            "properties": {
                "days_back": {
                    "type": "integer",
                    "description": "Number of days to look back (default 30)"
                }
            },
            "required": []
        },

        "executor": oa_get_machine_production,
        "chat_toolbox": True,
        "data_visualization": True,
        "default_chart_type": "line",

        "chart_config": {
            "x_axis": "ProductionDate",
            "series_by": "Machine",
            "y_axis": "PiecesProcessed",
            "y_axis_label": "Pieces Processed",
            "x_axis_label": "Date",
        },

        "normalizer": None,
    },


    {
        "name": "get_active_jobs",
        "description": "Get all active jobs from ScheduleShare. Optionally include on-hold jobs.",
        "category": "job_read",
        "display_category": "Jobs",

        "parameters": {
            "type": "object",
            "properties": {
                "include_on_hold": {
                    "type": "boolean",
                    "description": "Whether to include on-hold jobs (default false)"
                }
            },
            "required": []
        },

        "executor": oa_get_active_jobs,
        "chat_toolbox": True,
        "data_visualization": True,
        "default_chart_type": "table",
    },


    {
        "name": "get_jobs_by_pm",
        "description": "Get all jobs for a specific Project Manager from ScheduleShare.",
        "category": "job_read",
        "display_category": "Jobs",

        "parameters": {
            "type": "object",
            "properties": {
                "pm_name": {
                    "type": "string",
                    "description": "The Project Manager's name (e.g. 'John Smith')"
                },
                "active_only": {
                    "type": "boolean",
                    "description": "Whether to return only active jobs (default true)"
                }
            },
            "required": ["pm_name"]
        },

        "executor": oa_get_jobs_by_pm,
        "chat_toolbox": True,
        "data_visualization": True,
        "default_chart_type": "line",
        "chart_config": {
            "x_axis": "JobNumber",
            "y_axis": "TotalHours",
            "x_axis_label": "Job",
            "y_axis_label": "Total Hours"
        }
    },


    {
        "name": "get_jobs_shipping_soon",
        "description": "Get jobs shipping within a specified number of days. Useful for tracking upcoming deadlines.",
        "category": "job_read",
        "display_category": "Jobs",

        "parameters": {
            "type": "object",
            "properties": {
                "days_ahead": {
                    "type": "integer",
                    "description": "Number of days to look ahead (default 30)"
                }
            },
            "required": []
        },

        "executor": oa_get_jobs_shipping_soon,
        "chat_toolbox": True,
        "data_visualization": True,
        "default_chart_type": "line",
        "chart_config": {
            "x_axis": "JobNumber",
            "y_axis": "DaysUntilShip",
            "x_axis_label": "Job Number",
            "y_axis_label": "Days Until Ship",
        },
    },
]
