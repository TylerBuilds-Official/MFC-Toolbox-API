"""
Centralized Tool Registry

Aggregates tools from role-based modules and provides constants.

Structure:
- ROLE_HIERARCHY: Maps role names to permission levels
- TOOL_CATEGORIES: Maps category names to minimum role required
- TOOL_REGISTRY: Combined list of all tools from role modules

Tool modules are organized by minimum role required:
- user/     → Accessible by: user, manager, admin
- manager/  → Accessible by: manager, admin
- admin/    → Accessible by: admin only

Each role sees tools at their level and all levels below.
"""

# =============================================================================
# Role Hierarchy
# =============================================================================
# Higher number = more permissions
# A role can access anything at or below its level

ROLE_HIERARCHY = {
    "pending": 0,           # Newly registered, awaiting approval
    "user": 10,             # Standard user
    "manager": 100,         # Elevated access for supervisors/managers
#   "new_role_one": 200,    # Example new role
    "admin": 500,           # Full access
}


# =============================================================================
# Tool Categories
# =============================================================================
# Maps category name to minimum role required

TOOL_CATEGORIES = {
    # User-level categories
    "job_read": "user",             # View job data
    "reports": "user",              # Run production reports
    "memory": "user",               # Memory tools (search/save memories)
    "conversation": "user",         # Conversation tools (search/retrieve past conversations)
    "data_sessions": "user",        # Data session tools (search/retrieve past data sessions)
    "artifacts": "user",            # Artifact creation tools
    "company_info": "user",         # Company/employee lookups
    "filesystem": "user",           # Filesystem operations (via agent connector)
    
    # Manager-level categories
    "manager_reports": "manager",   # Sensitive reports (OT, labor costs, etc.)
    
    # Admin-level categories
    "job_write": "admin",           # Modify job data (future)
    "admin_tools": "admin",         # System administration
}


# =============================================================================
# Import Tools from Role Modules
# =============================================================================

from src.tools.tool_registry_modules.user import USER_TOOLS
from src.tools.tool_registry_modules.manager import MANAGER_TOOLS
from src.tools.tool_registry_modules.admin import ADMIN_TOOLS


# =============================================================================
# Combined Tool Registry
# =============================================================================

TOOL_REGISTRY: list[dict] = [
    *USER_TOOLS,
    *MANAGER_TOOLS,
    *ADMIN_TOOLS,
]


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "ROLE_HIERARCHY",
    "TOOL_CATEGORIES", 
    "TOOL_REGISTRY",
]
