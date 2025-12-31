"""
Service layer for DataResult operations.
"""
from src.tools.sql_tools.create_data_result import create_data_result
from src.tools.sql_tools.get_data_result import (
    get_data_result, 
    get_data_results_for_session,
    check_session_has_results
)
from src.utils.data_utils.data_result import DataResult, NormalizedResult


class DataResultService:

    @staticmethod
    def create_result(session_id: int, normalized: NormalizedResult) -> DataResult:
        """
        Creates a data result from a NormalizedResult.
        
        Args:
            session_id: The parent session ID
            normalized: NormalizedResult from tool execution
            
        Returns:
            DataResult object
        """
        data = create_data_result(
            session_id=session_id,
            columns=normalized.columns,
            rows=normalized.rows,
            row_count=normalized.row_count
        )
        return DataResultService._dict_to_result(data)

    @staticmethod
    def create_result_raw(
        session_id: int,
        columns: list[str],
        rows: list[list],
        row_count: int
    ) -> DataResult:
        """
        Creates a data result from raw components.
        
        Args:
            session_id: The parent session ID
            columns: List of column names
            rows: List of row data
            row_count: Total row count
            
        Returns:
            DataResult object
        """
        data = create_data_result(
            session_id=session_id,
            columns=columns,
            rows=rows,
            row_count=row_count
        )
        return DataResultService._dict_to_result(data)

    @staticmethod
    def get_result(session_id: int) -> DataResult | None:
        """
        Gets the result for a session.
        Returns most recent if multiple exist.
        
        Args:
            session_id: The session ID
            
        Returns:
            DataResult or None if not found
        """
        data = get_data_result(session_id)
        if data is None:
            return None
        return DataResultService._dict_to_result(data)

    @staticmethod
    def get_all_results(session_id: int) -> list[DataResult]:
        """
        Gets all results for a session.
        Use when session may have multiple results.
        
        Returns:
            List of DataResult objects
        """
        results_data = get_data_results_for_session(session_id)
        return [DataResultService._dict_to_result(r) for r in results_data]

    @staticmethod
    def has_results(session_id: int) -> bool:
        """
        Quick check if session has any results.
        
        Returns:
            True if results exist
        """
        return check_session_has_results(session_id)

    @staticmethod
    def _dict_to_result(data: dict) -> DataResult:
        """Convert raw dict from SQL to DataResult object."""
        return DataResult(
            id=data['id'],
            session_id=data['session_id'],
            columns=data['columns'],
            rows=data['rows'],
            row_count=data['row_count'],
            created_at=data['created_at'],
        )
