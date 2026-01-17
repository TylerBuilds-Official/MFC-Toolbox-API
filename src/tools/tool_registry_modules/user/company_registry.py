"""
Company Data Tools Registry - User Level

Accessible by: user, manager, admin
Category: company_info
Display Category: Company

AI-internal tools for looking up employee and company information.
Supports fuzzy name matching and department-based queries.
"""

from src.tools.local_mcp_tools.company_data import (
    oa_get_employee,
    oa_get_employee_email,
    oa_get_employee_phone,
    oa_get_employees_by_department,
    oa_get_project_managers,
    oa_get_it_team,
    oa_search_employees,
    oa_get_employee_directory_summary,
    oa_get_department_summary,
    oa_list_departments,
    oa_get_company_info,
    oa_get_contact_info,
    oa_get_all_company_data,
)


COMPANY_TOOLS = [
    {
        "name": "get_employee",
        "description": "Look up a specific employee's contact info by name. Supports fuzzy matching (e.g., 'blake', 'Blake Reed', 'blak' all work). Returns position, email, extension, and cell. Use for 'what's [name]'s email/phone/extension?'",
        "category": "company_info",
        "display_category": "Company",

        "parameters": {
            "type": "object",
            "properties": {
                "employee_name": {
                    "type": "string",
                    "description": "Full or partial employee name (e.g., 'blake', 'Blake Reed')"
                }
            },
            "required": ["employee_name"]
        },

        "executor": oa_get_employee,
        "chat_toolbox": False,
        "data_visualization": False,
    },


    {
        "name": "get_employee_email",
        "description": "Quick email lookup for a specific employee. Supports fuzzy name matching. Use when user just needs an email address.",
        "category": "company_info",
        "display_category": "Company",

        "parameters": {
            "type": "object",
            "properties": {
                "employee_name": {
                    "type": "string",
                    "description": "Full or partial employee name"
                }
            },
            "required": ["employee_name"]
        },

        "executor": oa_get_employee_email,
        "chat_toolbox": False,
        "data_visualization": False,
    },


    {
        "name": "get_employee_phone",
        "description": "Get phone contact info (extension and cell) for a specific employee. Supports fuzzy name matching.",
        "category": "company_info",
        "display_category": "Company",

        "parameters": {
            "type": "object",
            "properties": {
                "employee_name": {
                    "type": "string",
                    "description": "Full or partial employee name"
                }
            },
            "required": ["employee_name"]
        },

        "executor": oa_get_employee_phone,
        "chat_toolbox": False,
        "data_visualization": False,
    },


    {
        "name": "get_employees_by_department",
        "description": "List all employees in a department. Valid departments: executive, it, purchasing, project_mgmt, estimating, admin, safety, sales. Also accepts aliases like 'pm', 'tech', 'dev', 'office', 'leadership', 'exec'.",
        "category": "company_info",
        "display_category": "Company",

        "parameters": {
            "type": "object",
            "properties": {
                "department": {
                    "type": "string",
                    "description": "Department name or alias (e.g., 'it', 'project_mgmt', 'pm', 'exec')"
                }
            },
            "required": ["department"]
        },

        "executor": oa_get_employees_by_department,
        "chat_toolbox": False,
        "data_visualization": False,
    },


    {
        "name": "get_project_managers",
        "description": "Get all project managers. Shortcut for common query - returns list of PMs with contact info.",
        "category": "company_info",
        "display_category": "Company",

        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },

        "executor": oa_get_project_managers,
        "chat_toolbox": False,
        "data_visualization": False,
    },


    {
        "name": "get_it_team",
        "description": "Get all IT/Development team members. Returns list with contact info.",
        "category": "company_info",
        "display_category": "Company",

        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },

        "executor": oa_get_it_team,
        "chat_toolbox": False,
        "data_visualization": False,
    },


    {
        "name": "search_employees",
        "description": "Search employees by name, position, or email. Use as fallback when get_employee returns nothing, or for role-based queries like 'who handles purchasing' or 'find estimators'.",
        "category": "company_info",
        "display_category": "Company",

        "parameters": {
            "type": "object",
            "properties": {
                "search_term": {
                    "type": "string",
                    "description": "Search term to match against name, position, or email"
                }
            },
            "required": ["search_term"]
        },

        "executor": oa_search_employees,
        "chat_toolbox": False,
        "data_visualization": False,
    },


    {
        "name": "get_employee_directory_summary",
        "description": "Get a compact, scannable employee directory. Returns all employees with position and extension, one per line. Low token cost overview.",
        "category": "company_info",
        "display_category": "Company",

        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },

        "executor": oa_get_employee_directory_summary,
        "chat_toolbox": False,
        "data_visualization": False,
    },


    {
        "name": "get_department_summary",
        "description": "Get a summary of all departments and their members. Shows org structure at a glance.",
        "category": "company_info",
        "display_category": "Company",

        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },

        "executor": oa_get_department_summary,
        "chat_toolbox": False,
        "data_visualization": False,
    },


    {
        "name": "list_departments",
        "description": "Get list of valid department names. Use for disambiguation or when unsure which department to query.",
        "category": "company_info",
        "display_category": "Company",

        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },

        "executor": oa_list_departments,
        "chat_toolbox": False,
        "data_visualization": False,
    },


    {
        "name": "get_company_info",
        "description": "Get company information for MFC or Master Machining. Returns address, phone, fax, website, and description. Use 'mfc' (default) or 'mmm'/'master machining' for entity parameter.",
        "category": "company_info",
        "display_category": "Company",

        "parameters": {
            "type": "object",
            "properties": {
                "entity": {
                    "type": "string",
                    "description": "Which company: 'mfc' (default) or 'mmm' for Master Machining"
                }
            },
            "required": []
        },

        "executor": oa_get_company_info,
        "chat_toolbox": False,
        "data_visualization": False,
    },


    {
        "name": "get_contact_info",
        "description": "Get MFC office address, phone, fax, and website. Use for 'where is the office', 'company phone number', 'MFC address', directions questions.",
        "category": "company_info",
        "display_category": "Company",

        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },

        "executor": oa_get_contact_info,
        "chat_toolbox": False,
        "data_visualization": False,
    },


    {
        "name": "get_all_company_data",
        "description": "Get complete company data dump including all employees and business info. Use sparingly - prefer targeted tools for most queries. High token cost.",
        "category": "company_info",
        "display_category": "Company",

        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },

        "executor": oa_get_all_company_data,
        "chat_toolbox": False,
        "data_visualization": False,
    },
]
