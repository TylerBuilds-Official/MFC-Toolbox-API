# src/tools/sql_tools/__init__.py
"""
SQL Tools - Database operations for MFC Toolbox.

Organized by domain with facade exports for backward compatibility.
"""


# ============================================
# Connection Pools
# ============================================

from src.tools.sql_tools.pools.mssql_pool import get_mssql_connection, close_mssql_pool, SCHEMA
from src.tools.sql_tools.pools.mysql_pool import get_mysql_connection, close_mysql_pool
from src.tools.sql_tools.pools.voltron_pool import get_voltron_connection, close_voltron_pool


# ============================================
# Conversations
# ============================================

from src.tools.sql_tools.conversations.create_conversation import create_new_conversation
from src.tools.sql_tools.conversations.get_conversation import get_conversation
from src.tools.sql_tools.conversations.get_conversations_list import get_conversations_list
from src.tools.sql_tools.conversations.get_conversation_messages import get_conversation_messages
from src.tools.sql_tools.conversations.get_recent_conversations import get_recent_conversations
from src.tools.sql_tools.conversations.search_conversations import search_conversations
from src.tools.sql_tools.conversations.update_conversation import update_conversation
from src.tools.sql_tools.conversations.update_conversation_summary import update_conversation_summary
from src.tools.sql_tools.conversations.delete_conversation import delete_conversation


# ============================================
# Messages
# ============================================

from src.tools.sql_tools.messages.add_message import add_message
from src.tools.sql_tools.messages.get_message import get_message
from src.tools.sql_tools.messages.get_messages import get_messages
from src.tools.sql_tools.messages.admin_delete_messages import admin_delete_messages_for_conversation
from src.tools.sql_tools.messages.update_message_artifact import update_message_artifact


# ============================================
# Conversation State
# ============================================

from src.tools.sql_tools.conversation_state.get_conversation_state import get_conversation_state
from src.tools.sql_tools.conversation_state.upsert_conversation_state import upsert_conversation_state


# ============================================
# Memories
# ============================================

from src.tools.sql_tools.memories.get_user_memories import get_user_memories
from src.tools.sql_tools.memories.search_memories import search_memories
from src.tools.sql_tools.memories.get_memory import get_memory
from src.tools.sql_tools.memories.create_memory import create_memory
from src.tools.sql_tools.memories.update_memory import update_memory
from src.tools.sql_tools.memories.delete_memory import delete_memory


# ============================================
# User Settings
# ============================================

from src.tools.sql_tools.user_settings.get_user_settings import get_user_settings
from src.tools.sql_tools.user_settings.update_current_model import update_current_model
from src.tools.sql_tools.user_settings.update_provider import update_model_provider


# ============================================
# Data Sessions & Results
# ============================================

from src.tools.sql_tools.data_sessions.create_data_session import create_data_session
from src.tools.sql_tools.data_sessions.get_data_session import get_data_session
from src.tools.sql_tools.data_sessions.get_data_sessions_list import get_data_sessions_list, get_data_sessions_by_group
from src.tools.sql_tools.data_sessions.get_data_sessions_filtered import get_data_sessions_filtered
from src.tools.sql_tools.data_sessions.get_data_session_with_preview import get_data_session_with_preview
from src.tools.sql_tools.data_sessions.search_data_sessions import search_data_sessions
from src.tools.sql_tools.data_sessions.session_lineage import (
    get_root_session_id,
    get_session_lineage_by_root,
    get_full_session_lineage,
)
from src.tools.sql_tools.data_sessions.update_data_session import update_data_session, update_data_session_status, update_data_session_title, update_data_session_summary
from src.tools.sql_tools.data_sessions.soft_delete_data_session import soft_delete_data_session
from src.tools.sql_tools.data_sessions.create_data_result import create_data_result
from src.tools.sql_tools.data_sessions.get_data_result import get_data_result, get_data_results_for_session, check_session_has_results


# ============================================
# Data Session Groups
# ============================================

from src.tools.sql_tools.data_session_groups.create_data_session_group import create_data_session_group
from src.tools.sql_tools.data_session_groups.get_data_session_group import get_data_session_group, get_data_session_groups_by_user
from src.tools.sql_tools.data_session_groups.update_data_session_group import update_data_session_group
from src.tools.sql_tools.data_session_groups.delete_data_session_group import delete_data_session_group
from src.tools.sql_tools.data_session_groups.add_session_to_group import add_session_to_group
from src.tools.sql_tools.data_session_groups.remove_session_from_group import remove_session_from_group


# ============================================
# Conversation Projects
# ============================================

from src.tools.sql_tools.conversation_projects.create_conversation_project import create_conversation_project
from src.tools.sql_tools.conversation_projects.get_conversation_project import (
    get_conversation_project,
    get_conversation_projects_by_user,
)
from src.tools.sql_tools.conversation_projects.update_conversation_project import update_conversation_project
from src.tools.sql_tools.conversation_projects.delete_conversation_project import delete_conversation_project
from src.tools.sql_tools.conversation_projects.add_conversation_to_project import add_conversation_to_project
from src.tools.sql_tools.conversation_projects.remove_conversation_from_project import remove_conversation_from_project
from src.tools.sql_tools.conversation_projects.get_conversation_projects import get_conversation_projects
from src.tools.sql_tools.conversation_projects.get_project_conversations import get_project_conversations
from src.tools.sql_tools.conversation_projects.invite_to_project import invite_to_project
from src.tools.sql_tools.conversation_projects.get_pending_invites import get_pending_invites
from src.tools.sql_tools.conversation_projects.accept_project_invite import accept_project_invite
from src.tools.sql_tools.conversation_projects.decline_project_invite import decline_project_invite
from src.tools.sql_tools.conversation_projects.get_project_members import get_project_members
from src.tools.sql_tools.conversation_projects.remove_project_member import remove_project_member


# ============================================
# Artifacts
# ============================================

from src.tools.sql_tools.artifacts.create_artifact import create_artifact
from src.tools.sql_tools.artifacts.get_artifact import get_artifact
from src.tools.sql_tools.artifacts.get_artifacts_by_user import get_artifacts_by_user
from src.tools.sql_tools.artifacts.get_artifacts_by_conversation import get_artifacts_by_conversation
from src.tools.sql_tools.artifacts.record_artifact_access import record_artifact_access
from src.tools.sql_tools.artifacts.update_artifact import (
    update_artifact_metadata,
    update_artifact_status,
    update_artifact_generation_results,
)
from src.tools.sql_tools.artifacts.create_data_session_from_artifact import (
    create_data_session_from_artifact,
    get_existing_session_for_artifact,
)
from src.tools.sql_tools.artifacts.link_artifacts_to_message import link_artifacts_to_message


# ============================================
# Reporting (Voltron / MySQL)
# ============================================

from src.tools.sql_tools.reporting.get_jobs import get_jobs
from src.tools.sql_tools.reporting.get_job_info import get_job_info
from src.tools.sql_tools.reporting.get_machine_production import get_machine_production
from src.tools.sql_tools.reporting.get_ot_hours_by_job import get_ot_hours_by_job
from src.tools.sql_tools.reporting.get_ot_hours_all_jobs import get_ot_hours_all_jobs
from src.tools.sql_tools.reporting.get_active_jobs import get_active_jobs
# REMOVED: from src.tools.sql_tools.reporting.get_job_details import get_job_details
from src.tools.sql_tools.reporting.get_jobs_by_pm import get_jobs_by_pm
from src.tools.sql_tools.reporting.get_jobs_shipping_soon import get_jobs_shipping_soon


# ============================================
# __all__ Export List
# ============================================

__all__ = [
    # Pools
    "get_mssql_connection",
    "close_mssql_pool",
    "SCHEMA",
    "get_mysql_connection",
    "close_mysql_pool",
    "get_voltron_connection",
    "close_voltron_pool",
    
    # Conversations
    "create_new_conversation",
    "get_conversation",
    "get_conversations_list",
    "get_conversation_messages",
    "get_recent_conversations",
    "search_conversations",
    "update_conversation",
    "update_conversation_summary",
    "delete_conversation",
    
    # Messages
    "add_message",
    "get_message",
    "get_messages",
    "admin_delete_messages_for_conversation",
    "update_message_artifact",
    
    # Conversation State
    "get_conversation_state",
    "upsert_conversation_state",
    
    # Memories
    "get_user_memories",
    "search_memories",
    "get_memory",
    "create_memory",
    "update_memory",
    "delete_memory",
    
    # User Settings
    "get_user_settings",
    "update_current_model",
    "update_model_provider",
    
    # Data Sessions & Results
    "create_data_session",
    "get_data_session",
    "get_data_sessions_list",
    "get_data_sessions_by_group",
    "get_data_sessions_filtered",
    "get_data_session_with_preview",
    "search_data_sessions",
    "get_root_session_id",
    "get_session_lineage_by_root",
    "get_full_session_lineage",
    "update_data_session",
    "update_data_session_status",
    "update_data_session_title",
    "update_data_session_summary",
    "soft_delete_data_session",
    "create_data_result",
    "get_data_result",
    "get_data_results_for_session",
    "check_session_has_results",
    
    # Data Session Groups
    "create_data_session_group",
    "get_data_session_group",
    "get_data_session_groups_by_user",
    "update_data_session_group",
    "delete_data_session_group",
    "add_session_to_group",
    "remove_session_from_group",
    
    # Conversation Projects
    "create_conversation_project",
    "get_conversation_project",
    "get_conversation_projects_by_user",
    "update_conversation_project",
    "delete_conversation_project",
    "add_conversation_to_project",
    "remove_conversation_from_project",
    "get_conversation_projects",
    "get_project_conversations",
    "invite_to_project",
    "get_pending_invites",
    "accept_project_invite",
    "decline_project_invite",
    "get_project_members",
    "remove_project_member",
    
    # Artifacts
    "create_artifact",
    "get_artifact",
    "get_artifacts_by_user",
    "get_artifacts_by_conversation",
    "record_artifact_access",
    "update_artifact_metadata",
    "update_artifact_status",
    "update_artifact_generation_results",
    "create_data_session_from_artifact",
    "get_existing_session_for_artifact",
    "link_artifacts_to_message",
    
    # Reporting
    "get_jobs",
    "get_job_info",
    "get_machine_production",
    "get_ot_hours_by_job",
    "get_ot_hours_all_jobs",
    "get_active_jobs",
    # REMOVED: "get_job_details",
    "get_jobs_by_pm",
    "get_jobs_shipping_soon",
]
