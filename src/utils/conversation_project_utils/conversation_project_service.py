"""
Service layer for ConversationProject operations.
"""
from src.tools.sql_tools import (
    create_conversation_project,
    get_conversation_project,
    get_conversation_projects_by_user,
    update_conversation_project,
    delete_conversation_project,
    add_conversation_to_project,
    remove_conversation_from_project,
    get_conversation_projects,
    get_project_conversations,
    invite_to_project,
    get_pending_invites,
    accept_project_invite,
    decline_project_invite,
    get_project_members,
    remove_project_member,
)
from src.utils.conversation_project_utils.conversation_project import (
    ConversationProject,
    ProjectPermissions,
)
from src.utils.conversation_project_utils.project_member import ProjectMember
from src.utils.conversation_project_utils.project_invite import ProjectInvite


class ConversationProjectService:
    """Service for managing conversation projects."""

    # =========================================================================
    # Project CRUD
    # =========================================================================

    @staticmethod
    def create_project(
        owner_id: int,
        name: str,
        description: str = None,
        color: str = None,
        custom_instructions: str = None,
        project_type: str = 'private',
        permissions: ProjectPermissions = None
    ) -> ConversationProject:
        """
        Creates a new conversation project.
        
        Args:
            owner_id: The user creating the project
            name: Project name
            description: Optional description
            color: Optional color (hex or named)
            custom_instructions: Optional AI instructions
            project_type: 'private' | 'shared_locked' | 'shared_open'
            permissions: Optional permissions for shared_open projects
            
        Returns:
            ConversationProject object
        """
        permissions_dict = permissions.to_dict() if permissions else None
        
        project_id = create_conversation_project(
            owner_id=owner_id,
            name=name,
            description=description,
            color=color,
            custom_instructions=custom_instructions,
            project_type=project_type,
            permissions=permissions_dict
        )
        
        # Fetch the full project data
        data = get_conversation_project(project_id, owner_id)
        return ConversationProject.from_dict(data)

    @staticmethod
    def get_project(project_id: int, user_id: int = None) -> ConversationProject | None:
        """
        Retrieves a project by ID.
        
        Args:
            project_id: The project ID
            user_id: Optional user ID for access verification
            
        Returns:
            ConversationProject object or None if not found/no access
        """
        data = get_conversation_project(project_id, user_id)
        if data is None:
            return None
        return ConversationProject.from_dict(data)

    @staticmethod
    def list_projects(user_id: int) -> list[ConversationProject]:
        """
        Lists all projects for a user (owned + shared with them).
        
        Args:
            user_id: The user's ID
            
        Returns:
            List of ConversationProject objects, owned first then shared
        """
        projects_data = get_conversation_projects_by_user(user_id)
        return [ConversationProject.from_dict(p) for p in projects_data]

    @staticmethod
    def update_project(
        project_id: int,
        user_id: int,
        name: str = None,
        description: str = None,
        color: str = None,
        custom_instructions: str = None,
        project_type: str = None,
        permissions: ProjectPermissions = None
    ) -> ConversationProject | None:
        """
        Updates a project's properties.
        
        Convention:
            - None = don't change the field
            - '' (empty string) = clear the field
            - any other value = update the field
        
        Args:
            project_id: The project ID
            user_id: User ID for permission verification
            name: New name (None = no change)
            description: New description (None = no change, '' = clear)
            color: New color (None = no change, '' = clear)
            custom_instructions: New instructions (None = no change, '' = clear)
            project_type: New type (None = no change)
            permissions: New permissions (None = no change)
            
        Returns:
            Updated ConversationProject or None if failed
        """
        permissions_dict = None
        if permissions is not None:
            permissions_dict = permissions.to_dict() if permissions else {}
        
        success = update_conversation_project(
            project_id=project_id,
            user_id=user_id,
            name=name,
            description=description,
            color=color,
            custom_instructions=custom_instructions,
            project_type=project_type,
            permissions=permissions_dict
        )
        
        if not success:
            return None
        
        return ConversationProjectService.get_project(project_id, user_id)

    @staticmethod
    def delete_project(
        project_id: int,
        user_id: int,
        delete_conversations: bool = False
    ) -> bool:
        """
        Deletes a project (soft delete).
        
        Args:
            project_id: The project ID
            user_id: User ID for ownership verification
            delete_conversations: If True, deletes convos ONLY in this project
            
        Returns:
            True if delete succeeded
        """
        return delete_conversation_project(project_id, user_id, delete_conversations)

    # =========================================================================
    # Conversation <-> Project Membership
    # =========================================================================

    @staticmethod
    def add_conversation(
        conversation_id: int,
        project_id: int,
        user_id: int
    ) -> dict:
        """
        Adds a conversation to a project.
        
        Args:
            conversation_id: The conversation to add
            project_id: The project to add to
            user_id: User ID for permission verification
            
        Returns:
            Dict with 'success' and 'message'
        """
        return add_conversation_to_project(conversation_id, project_id, user_id)

    @staticmethod
    def remove_conversation(
        conversation_id: int,
        project_id: int,
        user_id: int
    ) -> bool:
        """
        Removes a conversation from a project.
        
        Args:
            conversation_id: The conversation to remove
            project_id: The project to remove from
            user_id: User ID for permission verification
            
        Returns:
            True if removal succeeded
        """
        return remove_conversation_from_project(conversation_id, project_id, user_id)

    @staticmethod
    def get_projects_for_conversation(
        conversation_id: int,
        user_id: int
    ) -> list[dict]:
        """
        Gets all projects a conversation belongs to.
        
        Args:
            conversation_id: The conversation ID
            user_id: User ID for ownership verification
            
        Returns:
            List of project summary dicts
        """
        return get_conversation_projects(conversation_id, user_id)

    @staticmethod
    def get_conversations_in_project(
        project_id: int,
        user_id: int
    ) -> list[dict]:
        """
        Gets all conversations in a project.
        
        Args:
            project_id: The project ID
            user_id: User ID for access verification
            
        Returns:
            List of conversation dicts with project membership info
        """
        return get_project_conversations(project_id, user_id)

    # =========================================================================
    # Invites
    # =========================================================================

    @staticmethod
    def invite_user(
        project_id: int,
        invited_email: str,
        invited_by: int,
        expires_in_days: int = 7
    ) -> dict:
        """
        Invites a user to a project by email.
        
        Args:
            project_id: The project ID
            invited_email: Email of user to invite
            invited_by: User ID of inviter
            expires_in_days: Days until invite expires
            
        Returns:
            Dict with 'invite_id' and 'message'
        """
        return invite_to_project(project_id, invited_email, invited_by, expires_in_days)

    @staticmethod
    def get_invites(user_email: str) -> list[ProjectInvite]:
        """
        Gets all pending invites for a user.
        
        Args:
            user_email: The user's email
            
        Returns:
            List of ProjectInvite objects
        """
        invites_data = get_pending_invites(user_email)
        return [ProjectInvite.from_dict(i) for i in invites_data]

    @staticmethod
    def accept_invite(
        invite_id: int,
        user_id: int,
        user_email: str
    ) -> dict:
        """
        Accepts a project invite.
        
        Args:
            invite_id: The invite ID
            user_id: The accepting user's ID
            user_email: The accepting user's email
            
        Returns:
            Dict with 'project_id' and 'message'
        """
        return accept_project_invite(invite_id, user_id, user_email)

    @staticmethod
    def decline_invite(invite_id: int, user_email: str) -> bool:
        """
        Declines a project invite.
        
        Args:
            invite_id: The invite ID
            user_email: The user's email
            
        Returns:
            True if decline succeeded
        """
        return decline_project_invite(invite_id, user_email)

    # =========================================================================
    # Members
    # =========================================================================

    @staticmethod
    def get_members(project_id: int, user_id: int) -> list[ProjectMember]:
        """
        Gets all members of a project.
        
        Args:
            project_id: The project ID
            user_id: User ID for access verification
            
        Returns:
            List of ProjectMember objects, owner first
        """
        members_data = get_project_members(project_id, user_id)
        return [ProjectMember.from_dict(m) for m in members_data]

    @staticmethod
    def remove_member(
        project_id: int,
        member_user_id: int,
        requested_by: int
    ) -> bool:
        """
        Removes a member from a project.
        
        Args:
            project_id: The project ID
            member_user_id: User ID to remove
            requested_by: User ID making the request
            
        Returns:
            True if removal succeeded
        """
        return remove_project_member(project_id, member_user_id, requested_by)
