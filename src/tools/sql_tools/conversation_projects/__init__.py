# src/tools/sql_tools/conversation_projects/__init__.py
"""
Conversation project operations for MFC Toolbox.
Handles project CRUD, membership, sharing, and invites.
"""

# Project CRUD
from src.tools.sql_tools.conversation_projects.create_conversation_project import create_conversation_project
from src.tools.sql_tools.conversation_projects.get_conversation_project import (
    get_conversation_project,
    get_conversation_projects_by_user,
)
from src.tools.sql_tools.conversation_projects.update_conversation_project import update_conversation_project
from src.tools.sql_tools.conversation_projects.delete_conversation_project import delete_conversation_project

# Conversation <-> Project membership
from src.tools.sql_tools.conversation_projects.add_conversation_to_project import add_conversation_to_project
from src.tools.sql_tools.conversation_projects.remove_conversation_from_project import remove_conversation_from_project
from src.tools.sql_tools.conversation_projects.get_conversation_projects import get_conversation_projects
from src.tools.sql_tools.conversation_projects.get_project_conversations import get_project_conversations

# Invites
from src.tools.sql_tools.conversation_projects.invite_to_project import invite_to_project
from src.tools.sql_tools.conversation_projects.get_pending_invites import get_pending_invites
from src.tools.sql_tools.conversation_projects.get_project_invites import get_project_invites
from src.tools.sql_tools.conversation_projects.accept_project_invite import accept_project_invite
from src.tools.sql_tools.conversation_projects.decline_project_invite import decline_project_invite
from src.tools.sql_tools.conversation_projects.cancel_project_invite import cancel_project_invite

# Members
from src.tools.sql_tools.conversation_projects.get_project_members import get_project_members
from src.tools.sql_tools.conversation_projects.remove_project_member import remove_project_member

# Community (Open Projects)
from src.tools.sql_tools.conversation_projects.get_community_projects import get_community_projects
from src.tools.sql_tools.conversation_projects.join_open_project import join_open_project


__all__ = [
    # Project CRUD
    "create_conversation_project",
    "get_conversation_project",
    "get_conversation_projects_by_user",
    "update_conversation_project",
    "delete_conversation_project",
    
    # Conversation <-> Project membership
    "add_conversation_to_project",
    "remove_conversation_from_project",
    "get_conversation_projects",
    "get_project_conversations",
    
    # Invites
    "invite_to_project",
    "get_pending_invites",
    "get_project_invites",
    "accept_project_invite",
    "decline_project_invite",
    "cancel_project_invite",
    
    # Members
    "get_project_members",
    "remove_project_member",
    
    # Community (Open Projects)
    "get_community_projects",
    "join_open_project",
]
