"""
Get data sessions with flexible filtering, sorting, and pagination.
Uses stored procedure: Toolbox_GetDataSessionsFiltered
"""
import json
from datetime import datetime
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_data_sessions_filtered(
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    tool_name: str = None,
    status: str = None,
    group_id: int = None,
    ungrouped: bool = False,
    sort_by: str = 'updated_at',
    sort_order: str = 'desc',
    after_date: str = None,
    before_date: str = None
) -> list[dict]:
    """
    Get data sessions with flexible filtering and sorting.
    
    Args:
        user_id: The user's ID
        limit: Max results (default 50, max 100)
        offset: Pagination offset
        tool_name: Filter by tool name
        status: Filter by status
        group_id: Filter by session group ID
        ungrouped: If True, return only sessions with no group
        sort_by: 'created_at' or 'updated_at' (default 'updated_at')
        sort_order: 'asc' or 'desc' (default 'desc')
        after_date: ISO date string - return sessions after this date
        before_date: ISO date string - return sessions before this date
        
    Returns:
        List of session dictionaries
    """
    # Validate and normalize sort options
    sort_by_col = 'UpdatedAt' if sort_by.lower() == 'updated_at' else 'CreatedAt'
    sort_order_sql = 'DESC' if sort_order.lower() == 'desc' else 'ASC'
    
    # Parse date strings to datetime if provided
    after_dt = None
    before_dt = None
    if after_date:
        try:
            after_dt = datetime.fromisoformat(after_date.replace('Z', '+00:00'))
        except ValueError:
            pass
    if before_date:
        try:
            before_dt = datetime.fromisoformat(before_date.replace('Z', '+00:00'))
        except ValueError:
            pass
    
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"""EXEC {SCHEMA}.Toolbox_GetDataSessionsFiltered 
                @UserId=?, @Limit=?, @Offset=?, @ToolName=?, @Status=?,
                @GroupId=?, @Ungrouped=?, @SortBy=?, @SortOrder=?,
                @AfterDate=?, @BeforeDate=?""",
            (
                user_id, limit, offset, tool_name, status,
                group_id, 1 if ungrouped else 0, sort_by_col, sort_order_sql,
                after_dt, before_dt
            )
        )
        
        rows = cursor.fetchall()
        cursor.close()
        
        sessions = []
        for row in rows:
            sessions.append({
                'id': row[0],
                'user_id': row[1],
                'message_id': row[2],
                'session_group_id': row[3],
                'parent_session_id': row[4],
                'tool_name': row[5],
                'tool_params': json.loads(row[6]) if row[6] else None,
                'visualization_config': json.loads(row[7]) if row[7] else None,
                'status': row[8],
                'error_message': row[9],
                'created_at': row[10],
                'updated_at': row[11],
                'title': row[12],
                'summary': row[13],
                'has_results': bool(row[14]),
                'row_count': row[15],
                'columns': json.loads(row[16]) if row[16] else None,
            })
        
        return sessions
