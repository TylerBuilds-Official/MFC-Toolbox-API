"""
Document Creation Tools Registry

Category: documents (user-level)
    NOTE: To adjust permission level, change category here and in TOOL_CATEGORIES

Display Category: Document Creation

Internal tools for AI-driven document generation.
Not exposed in toolbox UI - callable through natural language only.
"""

from src.tools.local_mcp_tools.document_creation import (
    oa_doc_create_html_report,
    oa_doc_save_raw_html,
    oa_doc_list_report_templates,
    oa_doc_get_report_skill,
    oa_doc_get_default_output_path,
)


DOCUMENT_CREATION_TOOLS = [
    {
        "name": "create_html_report",
        "description": (
            "Create an HTML report from a template with injected data. "
            "Use this for structured reports like job summaries, shipping lists, etc. "
            "IMPORTANT: Call list_report_templates first to see available templates AND "
            "learn the expected data format. Templates expect structured data with keys like "
            "'summary_cards', 'sections', 'tables' - not flat data objects."
        ),
        "category": "documents",  # NOTE: Change here to adjust permission level
        "display_category": "Document Creation",

        "parameters": {
            "type": "object",
            "properties": {
                "template_name": {
                    "type": "string",
                    "description": "Template file name (e.g., 'base_report.html')"
                },
                "data": {
                    "type": "object",
                    "description": "Structured data for the template. Should include keys like 'summary_cards', 'sections', 'tables'. Call list_report_templates first to see expected format."
                },
                "title": {
                    "type": "string",
                    "description": "Report title (optional, can also be in data)"
                },
                "output_filename": {
                    "type": "string",
                    "description": "Output filename (optional, auto-generated if not provided)"
                }
            },
            "required": ["template_name"]
        },

        "executor": oa_doc_create_html_report,
        "is_async": True,
        "needs_user_id": True,

        # Internal AI tool - not in toolbox UI
        "chat_toolbox": False,
        "data_visualization": False,
    },

    {
        "name": "save_raw_html",
        "description": (
            "Save raw HTML content directly to a file. "
            "Use this when generating complete custom HTML content. "
            "For standard reports, prefer create_html_report with templates."
        ),
        "category": "documents",
        "display_category": "Document Creation",

        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Complete HTML string to save"
                },
                "output_filename": {
                    "type": "string",
                    "description": "Output filename (e.g., 'custom_report.html')"
                }
            },
            "required": ["content", "output_filename"]
        },

        "executor": oa_doc_save_raw_html,
        "is_async": True,
        "needs_user_id": True,

        "chat_toolbox": False,
        "data_visualization": False,
    },

    {
        "name": "list_report_templates",
        "description": (
            "List available HTML report templates AND get skill documentation for data formatting. "
            "ALWAYS call this before create_html_report to understand the expected data structure. "
            "Returns template names, descriptions, and the skill guide with examples."
        ),
        "category": "documents",
        "display_category": "Document Creation",
        
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },
        
        "executor": oa_doc_list_report_templates,
        "is_async": True,
        "needs_user_id": True,
        
        "chat_toolbox": False,
        "data_visualization": False,
    },
    
    {
        "name": "get_report_skill",
        "description": (
            "Get the HTML report skill documentation. "
            "Read this to understand how to effectively use report creation tools, "
            "including data formatting, best practices, and examples."
        ),
        "category": "documents",
        "display_category": "Document Creation",
        
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },
        
        "executor": oa_doc_get_report_skill,
        "is_async": True,
        "needs_user_id": True,
        
        "chat_toolbox": False,
        "data_visualization": False,
    },
    
    {
        "name": "get_document_output_path",
        "description": (
            "Get the default output path where documents are saved. "
            "Useful for telling the user where to find their generated files."
        ),
        "category": "documents",
        "display_category": "Document Creation",
        
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },
        
        "executor": oa_doc_get_default_output_path,
        "is_async": True,
        "needs_user_id": True,
        
        "chat_toolbox": False,
        "data_visualization": False,
    },
]


__all__ = ["DOCUMENT_CREATION_TOOLS"]
