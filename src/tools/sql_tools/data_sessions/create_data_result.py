"""
Creates a data result for a session.
"""
import json
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


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
        
        # Use SET NOCOUNT ON to prevent row count messages from interfering
        # Use OUTPUT INTO with table variable to work with triggers
        cursor.execute(
            f"""
            SET NOCOUNT ON;
            
            DECLARE @InsertedResult TABLE (
                Id INT,
                SessionId INT,
                Columns NVARCHAR(MAX),
                Rows NVARCHAR(MAX),
                [RowCount] INT,
                CreatedAt DATETIME2
            );
            
            INSERT INTO {SCHEMA}.DataResults 
                (SessionId, Columns, Rows, [RowCount])
            OUTPUT 
                INSERTED.Id, INSERTED.SessionId, INSERTED.Columns, 
                INSERTED.Rows, INSERTED.[RowCount], INSERTED.CreatedAt
            INTO @InsertedResult
            VALUES (?, ?, ?, ?);
            
            SELECT * FROM @InsertedResult;
            """,
            (session_id, columns_json, rows_json, row_count)
        )
        
        row = cursor.fetchone()
        
        if not row:
            raise Exception("Failed to retrieve inserted result")
            
        cursor.close()
        
        return {
            'id': row[0],
            'session_id': row[1],
            'columns': json.loads(row[2]),
            'rows': json.loads(row[3]),
            'row_count': row[4],
            'created_at': row[5],
        }
