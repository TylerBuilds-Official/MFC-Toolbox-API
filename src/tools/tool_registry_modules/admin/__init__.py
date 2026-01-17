"""
Admin-Level Tools

Accessible by: admin only
System administration tools with full access.

Categories included:
- admin_tools → Admin display category (system management, user admin, etc.)

Note: Currently a placeholder. Add tools to system_registry.py as needed.
"""

from .system_registry import SYSTEM_TOOLS


ADMIN_TOOLS = [
    *SYSTEM_TOOLS,
]

__all__ = ["ADMIN_TOOLS"]
