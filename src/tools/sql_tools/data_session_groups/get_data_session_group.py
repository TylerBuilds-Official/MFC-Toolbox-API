"""
Retrieves data session groups for a user.
"""
from src.tools.sql_tools.pools import get_mssql_connection, SCHEMA


def get_data_session_groups_by_user(user_id: int) -> list[dict]:
    """
    Retrieves all data session groups for a user with session counts.
    
    Calls Toolbox_GetDataSessionGroupsByUser stored procedure.
    
    Args:
        user_id: The user's ID
        
    Returns:
        List of group dictionaries with session counts, ordered by UpdatedAt DESC
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            f"EXEC {SCHEMA}.Toolbox_GetDataSessionGroupsByUser @UserId = ?",
            (user_id,)
        )
        
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        
        # Consume any additional result sets
        while cursor.nextset():
            pass
        
        cursor.close()
        
        results = []
        for row in rows:
            record = dict(zip(columns, row))
            # Normalize column names to snake_case
            results.append({
                'id': record.get('Id'),
                'user_id': record.get('UserId'),
                'name': record.get('Name'),
                'description': record.get('Description'),
                'color': record.get('Color'),
                'created_at': record.get('CreatedAt'),
                'updated_at': record.get('UpdatedAt'),
                'session_count': record.get('SessionCount', 0),
            })
        
        return results


def get_data_session_group(group_id: int, user_id: int = None) -> dict | None:
    """
    Retrieves a single data session group by ID.
    
    Args:
        group_id: The group's ID
        user_id: Optional user ID for ownership verification
        
    Returns:
        Group dictionary or None if not found
    """
    with get_mssql_connection() as conn:
        cursor = conn.cursor()
        
        query = f"""
            SELECT 
                g.Id, g.UserId, g.Name, g.Description, g.Color,
                g.CreatedAt, g.UpdatedAt,
                COUNT(s.Id) AS SessionCount
            FROM {SCHEMA}.DataSessionGroups g
            LEFT JOIN {SCHEMA}.DataSessions s ON s.SessionGroupId = g.Id AND s.IsActive = 1
            WHERE g.Id = ?
        """
        params = [group_id]
        
        if user_id is not None:
            query += " AND g.UserId = ?"
            params.append(user_id)
        
        query += " GROUP BY g.Id, g.UserId, g.Name, g.Description, g.Color, g.CreatedAt, g.UpdatedAt"
        
        cursor.execute(query, params)
        row = cursor.fetchone()
        cursor.close()
        
        if not row:
            return None
        
        return {
            'id': row[0],
            'user_id': row[1],
            'name': row[2],
            'description': row[3],
            'color': row[4],
            'created_at': row[5],
            'updated_at': row[6],
            'session_count': row[7],
        }
