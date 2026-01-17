"""
Manager Reports Tools Registry - Manager Level

Accessible by: manager, admin
Category: manager_reports
Display Category: Overtime

Sensitive reports including overtime hours, labor costs, and other
manager-level data. Not visible to regular users.
"""

from src.tools.local_mcp_tools.local_mcp_tool_getOTHoursByJob import oa_get_ot_hours_by_job
from src.tools.local_mcp_tools.local_mcp_tool_getOTHoursAllJobs import oa_get_ot_hours_all_jobs


REPORTS_TOOLS = [
    {
        "name": "get_ot_hours_by_job",
        "description": "Get overtime hours for a specific job, broken down by employee. Shows who worked OT, total hours, and date ranges.",
        "category": "manager_reports",
        "display_category": "Overtime",

        "parameters": {
            "type": "object",
            "properties": {
                "job_number": {
                    "type": "string",
                    "description": "The job number to query (e.g. '6516')"
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format (defaults to 7 days ago)"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format (defaults to today)"
                }
            },
            "required": ["job_number"]
        },

        "executor": oa_get_ot_hours_by_job,
        "chat_toolbox": True,
        "data_visualization": True,
        "default_chart_type": "card",
        "chart_config": {
            "x_axis": "CLASTNAME",
            "y_axis": "TotalOTHours",
            "x_axis_label": "Employee",
            "y_axis_label": "OT Hours",
        },
    },


    {
        "name": "get_ot_hours_all_jobs",
        "description": "Get overtime hours summary across all jobs. Shows total OT per job, employee counts, and date ranges.",
        "category": "manager_reports",
        "display_category": "Overtime",

        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format (defaults to 7 days ago)"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format (defaults to today)"
                }
            },
            "required": []
        },

        "executor": oa_get_ot_hours_all_jobs,
        "chat_toolbox": True,
        "data_visualization": True,
        "default_chart_type": "bar",
        "chart_config": {
            "x_axis": "JobNumber",
            "y_axis": "TotalOTHours",
            "x_axis_label": "Job",
            "y_axis_label": "OT Hours",
        },
    },
]
