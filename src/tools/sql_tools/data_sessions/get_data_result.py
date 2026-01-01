"""
Retrieves data results for a session.
"""
import json
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_data_result(session_id: int) -> dict | None:
    """
    Retrieves the data result for a session.
    
    Note: Currently assumes one result per session.
    If multiple results exist, returns the most recent.
    
    Args:
        session_id: The session ID
        
    Returns:
        Dictionary with result fields, or None if not found.
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT TOP 1 Id, SessionId, Columns, Rows, [RowCount], CreatedAt
            FROM {SCHEMA}.DataResults
            WHERE SessionId = ?
            ORDER BY CreatedAt DESC
            """,
            (session_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        
        if row is None:
            return None
        
        return {
            'id': row[0],
            'session_id': row[1],
            'columns': json.loads(row[2]),
            'rows': json.loads(row[3]),
            'row_count': row[4],
            'created_at': row[5],
        }


def get_data_results_for_session(session_id: int) -> list[dict]:
    """
    Retrieves all data results for a session.
    Use when a session may have multiple results (versioned/paginated).
    
    Args:
        session_id: The session ID
        
    Returns:
        List of result dictionaries, ordered by CreatedAt DESC.
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT Id, SessionId, Columns, Rows, [RowCount], CreatedAt
            FROM {SCHEMA}.DataResults
            WHERE SessionId = ?
            ORDER BY CreatedAt DESC
            """,
            (session_id,)
        )
        rows = cursor.fetchall()
        cursor.close()
        
        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'session_id': row[1],
                'columns': json.loads(row[2]),
                'rows': json.loads(row[3]),
                'row_count': row[4],
                'created_at': row[5],
            })
        
        return results


def check_session_has_results(session_id: int) -> bool:
    """
    Quick check if a session has any results.
    Useful for populating 'has_results' flag without fetching payload.
    
    Args:
        session_id: The session ID
        
    Returns:
        True if at least one result exists.
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT COUNT(1) FROM {SCHEMA}.DataResults WHERE SessionId = ?
            """,
            (session_id,)
        )
        count = cursor.fetchone()[0]
        cursor.close()
        
        return count > 0
