"""
Document Creation Tools

Executor functions for document generation via agent.
Internal tools for AI orchestration - not exposed in toolbox UI.

Tools:
- create_html_report: Create report from template with data
- save_raw_html: Save AI-generated HTML directly
- list_report_templates: Get available templates
- get_report_skill: Get AI guidance for report creation
"""

from .tools import (
    oa_doc_create_html_report,
    oa_doc_save_raw_html,
    oa_doc_list_report_templates,
    oa_doc_get_report_skill,
    oa_doc_get_default_output_path,
)

__all__ = [
    "oa_doc_create_html_report",
    "oa_doc_save_raw_html",
    "oa_doc_list_report_templates",
    "oa_doc_get_report_skill",
    "oa_doc_get_default_output_path",
]
