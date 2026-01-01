"""
Service layer for DataSession operations.
"""

from src.tools.sql_tools import (create_data_session, get_data_session,
                                 get_data_sessions_list, get_data_sessions_by_group,
                                 update_data_session, update_data_session_status,
                                 check_session_has_results)

from src.utils.data_utils.data_session import DataSession, VisualizationConfig


class DataSessionService:

    @staticmethod
    def create_session(
        user_id: int,
        tool_name: str,
        tool_params: dict = None,
        message_id: int = None,
        parent_session_id: int = None,
        visualization_config: dict = None
    ) -> DataSession:
        """
        Creates a new data session with status='pending'.
        
        Args:
            user_id: The user creating the session
            tool_name: MCP tool identifier
            tool_params: Tool parameters as dict
            message_id: Optional message ID if spawned from chat
            parent_session_id: Optional parent session if this is a refinement
            visualization_config: Optional initial viz config
            
        Returns:
            DataSession object
        """
        data = create_data_session(
            user_id=user_id,
            tool_name=tool_name,
            tool_params=tool_params,
            message_id=message_id,
            parent_session_id=parent_session_id,
            visualization_config=visualization_config
        )
        return DataSessionService._dict_to_session(data)

    @staticmethod
    def get_session(session_id: int, user_id: int = None) -> DataSession | None:
        """
        Retrieves a session by ID.
        
        Args:
            session_id: The session ID
            user_id: Optional user ID for ownership verification
            
        Returns:
            DataSession object or None if not found
        """
        data = get_data_session(session_id, user_id)
        if data is None:
            return None
        return DataSessionService._dict_to_session(data)

    @staticmethod
    def list_sessions(
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        tool_name: str = None,
        status: str = None
    ) -> list[DataSession]:
        """
        Lists sessions for a user with optional filtering.
        
        Returns:
            List of DataSession objects
        """
        sessions_data = get_data_sessions_list(
            user_id=user_id,
            limit=limit,
            offset=offset,
            tool_name=tool_name,
            status=status
        )
        return [DataSessionService._dict_to_session(s) for s in sessions_data]

    @staticmethod
    def get_session_lineage(group_id: int, user_id: int = None) -> list[DataSession]:
        """
        Retrieves all sessions in a lineage group.
        
        Returns:
            List of DataSession objects ordered by creation time
        """
        sessions_data = get_data_sessions_by_group(group_id, user_id)
        return [DataSessionService._dict_to_session(s) for s in sessions_data]

    @staticmethod
    def update_session(session_id: int, user_id: int, updates: dict) -> DataSession | None:
        """
        Updates session fields.
        
        Args:
            session_id: The session ID
            user_id: User ID for ownership verification
            updates: Dict of fields to update (status, visualization_config, etc.)
            
        Returns:
            Updated DataSession or None if not found/not owned
        """
        success = update_data_session(session_id, user_id, updates)
        if not success:
            return None
        return DataSessionService.get_session(session_id, user_id)

    @staticmethod
    def set_status(session_id: int, status: str, error_message: str = None) -> bool:
        """
        Updates session status (internal use, no user verification).
        
        Args:
            session_id: The session ID
            status: New status (pending, running, success, error)
            error_message: Optional error message
            
        Returns:
            True if update succeeded
        """
        return update_data_session_status(session_id, status, error_message)

    @staticmethod
    def get_session_with_has_results(session_id: int, user_id: int = None) -> dict | None:
        """
        Gets session as dict with 'has_results' flag included.
        Useful for API responses where we want to indicate result availability.
        
        Returns:
            Session dict with has_results flag, or None
        """
        session = DataSessionService.get_session(session_id, user_id)
        if session is None:
            return None
        
        result = session.to_dict()
        result['has_results'] = check_session_has_results(session_id)
        return result

    @staticmethod
    def _dict_to_session(data: dict) -> DataSession:
        """Convert raw dict from SQL to DataSession object."""
        viz_config = None
        if data.get('visualization_config'):
            viz_config = VisualizationConfig.from_dict(data['visualization_config'])
        
        return DataSession(
            id=data['id'],
            user_id=data['user_id'],
            message_id=data.get('message_id'),
            session_group_id=data.get('session_group_id'),
            parent_session_id=data.get('parent_session_id'),
            tool_name=data['tool_name'],
            tool_params=data.get('tool_params'),
            visualization_config=viz_config,
            status=data['status'],
            error_message=data.get('error_message'),
            created_at=data['created_at'],
            updated_at=data['updated_at'],
        )
