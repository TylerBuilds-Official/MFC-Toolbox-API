"""
User-Level Tools

Accessible by: user, manager, admin
These tools form the base toolset available to all authenticated users.

Categories included:
- job_read     → Jobs display category
- reports      → Production display category
- memory       → Memory display category
- conversation → Conversations display category
- data_sessions → Data Sessions display category
- artifacts    → Artifacts display category
- company_info → Company display category
- filesystem   → Filesystem display category
"""

from .jobs_registry import JOB_TOOLS
from .memory_registry import MEMORY_TOOLS
from .conversation_registry import CONVERSATION_TOOLS
from .data_sessions_registry import DATA_SESSION_TOOLS
from .artifacts_registry import ARTIFACT_TOOLS
from .company_registry import COMPANY_TOOLS
from .filesystem_registry import FILESYSTEM_TOOLS


USER_TOOLS = [
    *JOB_TOOLS,
    *MEMORY_TOOLS,
    *CONVERSATION_TOOLS,
    *DATA_SESSION_TOOLS,
    *ARTIFACT_TOOLS,
    *COMPANY_TOOLS,
    *FILESYSTEM_TOOLS,
]

__all__ = ["USER_TOOLS"]
