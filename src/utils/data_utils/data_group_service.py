"""
Service layer for DataGroup operations.
"""
from src.tools.sql_tools import (
    create_data_session_group,
    get_data_session_group,
    get_data_session_groups_by_user,
    update_data_session_group,
    delete_data_session_group,
    add_session_to_group,
    remove_session_from_group,
)
from src.utils.data_utils.data_group import DataGroup


class DataGroupService:
    """Service for managing data session groups."""

    @staticmethod
    def create_group(
        user_id: int,
        name: str,
        description: str = None,
        color: str = None
    ) -> DataGroup:
        """
        Creates a new data session group.
        
        Args:
            user_id: The user creating the group
            name: Group name
            description: Optional description
            color: Optional color (hex or named)
            
        Returns:
            DataGroup object
        """
        group_id = create_data_session_group(
            user_id=user_id,
            name=name,
            description=description,
            color=color
        )
        
        # Fetch the full group data
        data = get_data_session_group(group_id, user_id)
        return DataGroup.from_dict(data)

    @staticmethod
    def get_group(group_id: int, user_id: int = None) -> DataGroup | None:
        """
        Retrieves a group by ID.
        
        Args:
            group_id: The group ID
            user_id: Optional user ID for ownership verification
            
        Returns:
            DataGroup object or None if not found
        """
        data = get_data_session_group(group_id, user_id)
        if data is None:
            return None
        return DataGroup.from_dict(data)

    @staticmethod
    def list_groups(user_id: int) -> list[DataGroup]:
        """
        Lists all groups for a user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            List of DataGroup objects ordered by UpdatedAt DESC
        """
        groups_data = get_data_session_groups_by_user(user_id)
        return [DataGroup.from_dict(g) for g in groups_data]

    @staticmethod
    def update_group(
        group_id: int,
        user_id: int,
        name: str = None,
        description: str = None,
        color: str = None
    ) -> DataGroup | None:
        """
        Updates a group's properties.
        
        Convention:
            - None = don't change the field
            - '' (empty string) = clear the field
            - any other value = update the field
        
        Args:
            group_id: The group ID
            user_id: User ID for ownership verification
            name: New name (None = no change)
            description: New description (None = no change, '' = clear)
            color: New color (None = no change, '' = clear)
            
        Returns:
            Updated DataGroup or None if not found/not owned
        """
        success = update_data_session_group(
            group_id=group_id,
            user_id=user_id,
            name=name,
            description=description,
            color=color
        )
        
        if not success:
            return None
        
        # Fetch and return the updated group
        return DataGroupService.get_group(group_id, user_id)

    @staticmethod
    def delete_group(group_id: int, user_id: int) -> bool:
        """
        Deletes a group. Sessions in the group are unlinked, not deleted.
        
        Args:
            group_id: The group ID
            user_id: User ID for ownership verification
            
        Returns:
            True if delete succeeded, False if not found/not owned
        """
        return delete_data_session_group(group_id, user_id)

    @staticmethod
    def add_session(session_id: int, group_id: int, user_id: int) -> bool:
        """
        Adds a session to a group.
        
        Args:
            session_id: The session ID to add
            group_id: The group ID to add to
            user_id: User ID for ownership verification
            
        Returns:
            True if assignment succeeded
        """
        return add_session_to_group(session_id, group_id, user_id)

    @staticmethod
    def remove_session(session_id: int, user_id: int) -> bool:
        """
        Removes a session from its current group.
        
        Args:
            session_id: The session ID
            user_id: User ID for ownership verification
            
        Returns:
            True if removal succeeded
        """
        return remove_session_from_group(session_id, user_id)
