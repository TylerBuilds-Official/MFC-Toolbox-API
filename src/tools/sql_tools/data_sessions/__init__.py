# src/tools/sql_tools/data_sessions/__init__.py
"""
Data session and result operations for MFC Toolbox.
"""

from src.tools.sql_tools.data_sessions.create_data_session import create_data_session
from src.tools.sql_tools.data_sessions.get_data_session import get_data_session
from src.tools.sql_tools.data_sessions.get_data_sessions_list import (
    get_data_sessions_list,
    get_data_sessions_by_group,
)
from src.tools.sql_tools.data_sessions.get_data_sessions_filtered import get_data_sessions_filtered
from src.tools.sql_tools.data_sessions.get_data_session_with_preview import get_data_session_with_preview
from src.tools.sql_tools.data_sessions.search_data_sessions import search_data_sessions
from src.tools.sql_tools.data_sessions.session_lineage import (
    get_root_session_id,
    get_session_lineage_by_root,
    get_full_session_lineage,
)
from src.tools.sql_tools.data_sessions.update_data_session import (
    update_data_session,
    update_data_session_status,
    update_data_session_title,
    update_data_session_summary,
)
from src.tools.sql_tools.data_sessions.soft_delete_data_session import soft_delete_data_session
from src.tools.sql_tools.data_sessions.create_data_result import create_data_result
from src.tools.sql_tools.data_sessions.get_data_result import (
    get_data_result,
    get_data_results_for_session,
    check_session_has_results,
)

__all__ = [
    # Sessions - CRUD
    "create_data_session",
    "get_data_session",
    "get_data_sessions_list",
    "get_data_sessions_by_group",
    "get_data_sessions_filtered",
    "get_data_session_with_preview",
    "update_data_session",
    "update_data_session_status",
    "update_data_session_title",
    "update_data_session_summary",
    "soft_delete_data_session",
    # Sessions - Search
    "search_data_sessions",
    # Sessions - Lineage
    "get_root_session_id",
    "get_session_lineage_by_root",
    "get_full_session_lineage",
    # Results
    "create_data_result",
    "get_data_result",
    "get_data_results_for_session",
    "check_session_has_results",
]
