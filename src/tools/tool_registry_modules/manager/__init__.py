"""
Manager-Level Tools

Accessible by: manager, admin
Includes sensitive reports and data not available to regular users.

Categories included:
- manager_reports → Overtime display category (OT hours, labor costs)
"""

from .reports_registry import REPORTS_TOOLS


MANAGER_TOOLS = [
    *REPORTS_TOOLS,
]

__all__ = ["MANAGER_TOOLS"]
