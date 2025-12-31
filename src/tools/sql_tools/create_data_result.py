"""
Creates a data result for a session.
"""
import json
from src.tools.sql_tools import get_mssql_connection
from src.tools.sql_tools.mssql_pool import SCHEMA


def create_data_result(
    session_id: int,
    columns: list[str],
    rows: list[list],
    row_count: int
) -> dict:
    """
    Creates a data result record for a session.
    
    Args:
        session_id: The parent session ID
        columns: List of column names
        rows: List of row data (each row is a list of values)
        row_count: Total number of rows
        
    Returns:
        Dictionary with all result fields including the new Id.
    """
    columns_json = json.dumps(columns)
    rows_json = json.dumps(rows)
    
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO {SCHEMA}.DataResults 
                (SessionId, Columns, Rows, [RowCount])
            OUTPUT 
                INSERTED.Id, INSERTED.SessionId, INSERTED.Columns, 
                INSERTED.Rows, INSERTED.[RowCount], INSERTED.CreatedAt
            VALUES (?, ?, ?, ?)
            """,
            (session_id, columns_json, rows_json, row_count)
        )
        row = cursor.fetchone()
        cursor.close()
        
        return {
            'id': row[0],
            'session_id': row[1],
            'columns': json.loads(row[2]),
            'rows': json.loads(row[3]),
            'row_count': row[4],
            'created_at': row[5],
        }
